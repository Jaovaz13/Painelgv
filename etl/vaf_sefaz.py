#!/usr/bin/env python
"""
ETL para extração de dados do VAF (Valor Adicionado Fiscal)
Fonte: SEFAZ-MG - Secretaria da Fazenda de Minas Gerais

POLÍTICA: 100% DADOS REAIS
-API SEFAZ-MG (se disponível)
- Fallback: arquivo em data/raw/vaf_sefaz.csv
- NUNCA gera dados simulados
"""
import logging
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_session, Indicator
from config import DATA_DIR

logger = logging.getLogger(__name__)

# URLs da API SEFAZ-MG
SEFAZ_API_BASE = "https://api.sefaz.mg.gov.br"


def load_vaf_from_raw() -> Optional[Dict]:
    """
    Carrega VAF de arquivo CSV em data/raw se disponível.
    Formato esperado: ano;valor
    """
    try:
        csv_path = DATA_DIR / "raw" / "vaf_sefaz.csv"
        if not csv_path.exists():
            logger.warning(f"Arquivo {csv_path} não encontrado")
            return None
            
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        logger.info(f"Carregando VAF de {csv_path}")
        
        data = {
            "municipio": "Governador Valadares",
            "codigo_ibge": "3127701",
            "vaf": {}
        }
        
        for _, row in df.iterrows():
            year = str(int(row['ano']))
            value = float(row['valor'])
            data["vaf"][year] = value
        
        logger.info(f"VAF carregado de {csv_path}: {len(df)} registros")
        return data
        
    except Exception as e:
        logger.error(f"Erro ao carregar VAF de /raw: {e}")
        return None


def extrair_vaf_municipal() -> Optional[Dict]:
    """
    Extrai dados do VAF para o município.
    
    Prioridade:
    1. API SEFAZ-MG (se disponível)
    2. Arquivo local em data/raw/vaf_sefaz.csv
    3. Retorna None (sem dados disponíveis)
    """
    try:
        # Tenta API SEFAZ-MG
        url = f"{SEFAZ_API_BASE}/vaf/municipios/3127701"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data:
                logger.info("VAF obtido da API SEFAZ-MG")
                return data
        
        # Se API não estiver disponível, tenta arquivo local
        logger.warning("API SEFAZ não disponível, tentando arquivo local em data/raw")
        return load_vaf_from_raw()
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados do VAF: {e}")
        # Tenta arquivo local como último recurso
        return load_vaf_from_raw()


def processar_serie_vaf(dados: Dict) -> List[Dict]:
    """Processa série histórica do VAF"""
    serie = []
    
    vaf_data = dados.get("vaf", {})
    for ano, valor in vaf_data.items():
        if valor and valor != "null":
            try:
                serie.append({
                    "Ano": int(ano),
                    "Valor": float(valor),
                    "Variavel": "RECEITA_VAF"
                })
            except (ValueError, TypeError):
                continue
    
    return serie


def salvar_vaf_no_banco(session, dados: List[Dict]):
    """Salva dados do VAF no banco de dados"""
    for item in dados:
        # Verificar se já existe para evitar violação de constraint
        existing = session.query(Indicator).filter_by(
            indicator_key="RECEITA_VAF",
            source="SEFAZ_MG",
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
                indicator_key="RECEITA_VAF",
                source="SEFAZ_MG",
                year=item["Ano"],
                value=item["Valor"],
                municipality_code="3127701",
                municipality_name="Governador Valadares",
                uf="MG",
                unit="R$",
                collected_at=datetime.now()
            )
            session.add(indicator)
    
    logger.info(f"Salvos {len(dados)} registros de VAF")


def run_etl_vaf_sefaz():
    """Executa ETL completo para dados do VAF"""
    logger.info("Iniciando ETL para dados do VAF")
    
    session = get_session()
    
    try:
        # Extrair dados do VAF
        logger.info("Extraindo dados do VAF...")
        dados_vaf = extrair_vaf_municipal()
        if dados_vaf:
            serie_vaf = processar_serie_vaf(dados_vaf)
            if serie_vaf:
                salvar_vaf_no_banco(session, serie_vaf)
            else:
                logger.warning("Nenhum dado de VAF encontrado")
        else:
            logger.error(
                "Falha ao extrair dados do VAF. "
                "Verifique: (1) API SEFAZ-MG, (2) arquivo data/raw/vaf_sefaz.csv"
            )
        
        session.commit()
        logger.info("ETL para dados do VAF concluído com sucesso")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Erro no ETL do VAF: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
    run_etl_vaf_sefaz()
