#!/usr/bin/env python
"""
Script de auditoria completa dos dados no banco
Verifica a atualização de todos os indicadores
"""
import sys
import os
sys.path.append(os.getcwd())

from database import get_session, Indicator
from sqlalchemy import func
import pandas as pd
from datetime import datetime

def audit_all_indicators():
    """Audita todos os indicadores no banco de dados"""
    session = get_session()
    
    print("=" * 80)
    print("AUDITORIA COMPLETA DE DADOS - Painel GV")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Busca todos os indicadores únicos
    indicators = session.query(
        Indicator.indicator_key,
        Indicator.source,
        Indicator.category,
        func.min(Indicator.year).label('ano_min'),
        func.max(Indicator.year).label('ano_max'),
        func.count(Indicator.id).label('total_registros')
    ).group_by(
        Indicator.indicator_key,
        Indicator.source,
        Indicator.category
    ).order_by(
        Indicator.category,
        Indicator.indicator_key
    ).all()
    
    # Organiza por categoria
    by_category = {}
    for ind in indicators:
        cat = ind.category or "Sem Categoria"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(ind)
    
    # Exibe por categoria
    total_indicators = 0
    total_records = 0
    
    for category in sorted(by_category.keys()):
        print(f"\n[{category}]")
        print("-" * 80)
        
        for ind in by_category[category]:
            total_indicators += 1
            total_records += ind.total_registros
            
            # Calcula anos de cobertura
            anos_cobertura = ind.ano_max - ind.ano_min + 1 if ind.ano_max and ind.ano_min else 0
            
            # Verifica se está atualizado (último ano >= 2021)
            status = "[OK]" if ind.ano_max and ind.ano_max >= 2021 else "[!!]"
            
            print(f"{status} {ind.indicator_key:30s} | {ind.source:15s} | "
                  f"{ind.ano_min}-{ind.ano_max} ({anos_cobertura:2d} anos) | "
                  f"{ind.total_registros:4d} registros")
    
    print("\n" + "=" * 80)
    print(f"RESUMO GERAL")
    print("=" * 80)
    print(f"Total de indicadores únicos: {total_indicators}")
    print(f"Total de registros no banco: {total_records}")
    
    # Indicadores desatualizados (último ano < 2021)
    outdated = [ind for cat in by_category.values() for ind in cat if ind.ano_max and ind.ano_max < 2021]
    if outdated:
        print(f"\n[ATENCAO] INDICADORES DESATUALIZADOS ({len(outdated)}):")
        for ind in outdated:
            print(f"   - {ind.indicator_key} ({ind.source}): ultimo ano = {ind.ano_max}")
    
    # Indicadores sem dados
    no_data_indicators = session.query(Indicator.indicator_key).distinct().count()
    print(f"\nTotal de chaves de indicadores distintas: {no_data_indicators}")
    
    session.close()
    
    print("\n" + "=" * 80)
    print("AUDITORIA CONCLUÍDA")
    print("=" * 80)

if __name__ == "__main__":
    audit_all_indicators()
