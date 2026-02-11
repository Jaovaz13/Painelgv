#!/usr/bin/env python
"""
ETL para Sinopse Estatística da Educação Básica.

IMPORTANTE:
- Este módulo originalmente criava dados SIMULADOS apenas para testes.
- Por política institucional do PAINEL GV, é proibido o uso de dados simulados.
- Os indicadores de educação devem ser alimentados exclusivamente por dados reais,
  preferencialmente a partir dos arquivos em `data/raw/Sinopse_Estatistica_da_Educação_Basica_*`.

Por isso, toda a lógica de geração de números artificiais foi desativada. O ETL real
de educação deve ser feito pelos módulos `educacao_inep.py`, `educacao_real.py` e
`ideb.py`, que usam APIs oficiais e arquivos reais em `/raw`.
"""
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_session, Indicator

logger = logging.getLogger(__name__)

def criar_dados_simulados_sinopse() -> List[Dict]:
    """
    [DESATIVADO] Antes gerava dados simulados de Sinopse para testes.
    
    Mantido apenas por compatibilidade de import, mas NÃO deve ser usado.
    Qualquer chamada a esta função indica uso incorreto de dados não reais.
    """
    logger.error(
        "criar_dados_simulados_sinopse() foi chamado, mas geração de dados simulados "
        "é proibida no PAINEL GV. Nenhum dado foi criado."
    )
    return []

def salvar_sinopse_no_banco(session, dados: List[Dict]):
    """Salva dados da Sinopse no banco de dados"""
    for item in dados:
        # Verificar se já existe para evitar violação de constraint
        existing = session.query(Indicator).filter_by(
            indicator_key="ESCOLAS_FUNDAMENTAL",
            source="INEP_SINOPSE",
            year=item["Ano"]
        ).first()
        
        if existing:
            # Atualiza registro existente
            existing.value = item["Valor"]
            existing.collected_at = datetime.now()
            session.commit()
        else:
            # Cria novo registro
            indicator = Indicator(
                indicator_key="ESCOLAS_FUNDAMENTAL",
                source="INEP_SINOPSE",
                year=item["Ano"],
                value=item["Valor"],
                municipality_code="3127701",
                municipality_name="Governador Valadares",
                uf="MG",
                collected_at=datetime.now()
            )
            session.add(indicator)
    
    logger.info(f"Salvos {len(dados)} registros de Escolas Fundamentais")

def run_etl_sinopse_educacao():
    """
    [DESATIVADO] ETL de Sinopse com dados simulados.
    
    Este runner é mantido apenas para não quebrar importações antigas, mas não executa
    mais nenhuma inserção de dados. O fluxo oficial de educação deve utilizar apenas
    ETLs baseados em dados reais (APIs oficiais e arquivos em `data/raw`).
    """
    logger.warning(
        "run_etl_sinopse_educacao() chamado, mas o ETL de Sinopse baseado em dados "
        "simulados está desativado. Nenhum dado foi gravado."
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
    run_etl_sinopse_educacao()
