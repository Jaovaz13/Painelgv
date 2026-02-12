#!/usr/bin/env python
"""
ETL para extração de dados do ICMS
Fonte: SEFAZ-MG - Secretaria da Fazenda de Minas Gerais

POLÍTICA: 100% DADOS REAIS
- API SEFAZ-MG (se disponível)
- Fallback: arquivo em data/raw/icms_sefaz.csv
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


def load_icms_from_raw() -> Optional[Dict]:
    """
    Carrega ICMS de arquivo CSV em data/raw se disponível.
    Formato esperado: ano;valor
    """
    try:
        csv_path = DATA_DIR / "raw" / "icms_sefaz.csv"
        if not csv_path.exists():
            logger.warning(f"Arquivo {csv_path} não encontrado")
            return None
            
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        logger.info(f"Carregando ICMS de {csv_path}")
        
        data = {
            "municipio": "Governador Valadares",
            "codigo_ibge": "3127701",
            "icms": {}
        }
        
        for _, row in df.iterrows():
            year = str(int(row['ano']))
            value = float(row['valor'])
            data["icms"][year] = value
        
        logger.info(f"ICMS carregado de {csv_path}: {len(df)} registros")
        return data
        
    except Exception as e:
        logger.error(f"Erro ao carregar ICMS de /raw: {e}")
        return None


def extrair_icms_municipal() -> Optional[Dict]:
    """
    Extrai dados do ICMS para o município.
    
    Prioridade:
    1. API SEFAZ-MG (se disponível)
    2. Arquivo local em data/raw/icms_sefaz.csv
    3. Retorna None (sem dados disponíveis)
    """
    try:
        # Tenta API SEFAZ-MG
        url = f"{SEFAZ_API_BASE}/icms/municipios/3127701"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data:
                logger.info("ICMS obtido da API SEFAZ-MG")
                return data
        
        # Se API não estiver disponível, tenta arquivo local
        logger.warning("API SEFAZ não disponível, tentando arquivo local em data/raw")
        return load_icms_from_raw()
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados do ICMS: {e}")
        # Tenta arquivo local como último recurso
        return load_icms_from_raw()


def processar_serie_icms(dados: Dict) -> List[Dict]:
    """Processa série histórica do ICMS"""
    serie = []
    
    icms_data = dados.get("icms", {})
    for ano, valor in icms_data.items():
        if valor and valor != "null":
            try:
                serie.append({
                    "Ano": int(ano),
                    "Valor": float(valor),
                    "Variavel": "RECEITA_ICMS"
                })
            except (ValueError, TypeError):
                continue
    
    return serie


def salvar_icms_no_banco(dados: List[Dict]):
    """Salva dados do ICMS no banco de dados usando upsert_indicators"""
    if not dados:
        return
        
    df = pd.DataFrame(dados)
    df = df.rename(columns={"Ano": "year", "Valor": "value"})
    
    upsert_indicators(
        df,
        indicator_key="RECEITA_ICMS",
        source="SEFAZ_MG",
        category="Economia"
    )


def run_etl_icms_sefaz():
    """Executa ETL completo para dados do ICMS"""
    logger.info("Iniciando ETL para dados do ICMS")
    
    try:
        # Extrair dados do ICMS
        logger.info("Extraindo dados do ICMS...")
        dados_icms = extrair_icms_municipal()
        if dados_icms:
            serie_icms = processar_serie_icms(dados_icms)
            if serie_icms:
                salvar_icms_no_banco(serie_icms)
            else:
                logger.warning("Nenhum dado de ICMS encontrado")
        else:
            logger.error(
                "Falha ao extrair dados do ICMS. "
                "Verifique: (1) API SEFAZ-MG, (2) arquivo data/raw/icms_sefaz.csv"
            )
        
        logger.info("ETL para dados do ICMS concluído com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no ETL do ICMS: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
    run_etl_icms_sefaz()
