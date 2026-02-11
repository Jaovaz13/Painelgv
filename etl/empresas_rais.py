#!/usr/bin/env python
"""
ETL para extração de dados de Número de Empresas
Fonte: RAIS - Relação Anual de Informações Sociais

POLÍTICA: 100% DADOS REAIS
- API RAIS (se disponível)
- Fallback: arquivo em data/raw/empresas_rais.csv
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

# URLs da API RAIS
RAIS_API_BASE = "https://api.rais.gov.br"


def load_empresas_from_raw() -> Optional[Dict]:
    """
    Carrega dados de empresas de arquivo CSV em data/raw se disponível.
    Formato esperado: ano;valor
    """
    try:
        csv_path = DATA_DIR / "raw" / "empresas_rais.csv"
        if not csv_path.exists():
            logger.warning(f"Arquivo {csv_path} não encontrado")
            return None
            
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        logger.info(f"Carregando dados de empresas de {csv_path}")
        
        data = {
            "municipio": "Governador Valadares",
            "codigo_ibge": "3127701",
            "empresas": {}
        }
        
        for _, row in df.iterrows():
            year = str(int(row['ano']))
            value = float(row['valor'])
            data["empresas"][year] = value
        
        logger.info(f"Dados de empresas carregados de {csv_path}: {len(df)} registros")
        return data
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados de empresas de /raw: {e}")
        return None


def extrair_empresas_municipais() -> Optional[Dict]:
    """
    Extrai dados de número de empresas para o município.
    
    Prioridade:
    1. API RAIS (se disponível)
    2. Arquivo local em data/raw/empresas_rais.csv
    3. Retorna None (sem dados disponíveis)
    """
    try:
        # Tenta URL oficial da API RAIS
        url = f"{RAIS_API_BASE}/empresas/municipios/3127701"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data:
                logger.info("Dados de empresas obtidos da API RAIS")
                return data
        
        # Se API não estiver disponível, tenta arquivo local
        logger.warning("API RAIS não disponível, tentando arquivo local em data/raw")
        return load_empresas_from_raw()
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados de empresas: {e}")
        # Tenta arquivo local como último recurso
        return load_empresas_from_raw()


def processar_serie_empresas(dados: Dict) -> List[Dict]:
    """Processa série histórica de número de empresas"""
    serie = []
    
    empresas_data = dados.get("empresas", {})
    for ano, valor in empresas_data.items():
        if valor and valor != "null":
            try:
                serie.append({
                    "Ano": int(ano),
                    "Valor": float(valor),
                    "Variavel": "NUM_EMPRESAS"
                })
            except (ValueError, TypeError):
                continue
    
    return serie


def salvar_empresas_no_banco(session, dados: List[Dict]):
    """Salva dados de empresas no banco de dados"""
    for item in dados:
        # Verificar se já existe para evitar violação de constraint
        existing = session.query(Indicator).filter_by(
            indicator_key="NUM_EMPRESAS",
            source="RAIS",
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
                indicator_key="NUM_EMPRESAS",
                source="RAIS",
                year=item["Ano"],
                value=item["Valor"],
                municipality_code="3127701",
                municipality_name="Governador Valadares",
                uf="MG",
                unit="Unidades",
                collected_at=datetime.now()
            )
            session.add(indicator)
    
    logger.info(f"Salvos {len(dados)} registros de Número de Empresas")


def run_etl_empresas_rais():
    """Executa ETL completo para dados de Número de Empresas"""
    logger.info("Iniciando ETL para dados de Número de Empresas")
    
    session = get_session()
    
    try:
        # Extrair dados de empresas
        logger.info("Extraindo dados de Número de Empresas...")
        dados_empresas = extrair_empresas_municipais()
        if dados_empresas:
            serie_empresas = processar_serie_empresas(dados_empresas)
            if serie_empresas:
                salvar_empresas_no_banco(session, serie_empresas)
            else:
                logger.warning("Nenhum dado de empresas encontrado")
        else:
            logger.error(
                "Falha ao extrair dados de empresas. "
                "Verifique: (1) API RAIS, (2) arquivo data/raw/empresas_rais.csv"
            )
        
        session.commit()
        logger.info("ETL para dados de Número de Empresas concluído com sucesso")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Erro no ETL de Empresas: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
    run_etl_empresas_rais()
