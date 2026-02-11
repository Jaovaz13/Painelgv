#!/usr/bin/env python
"""
ETL para extração de dados do PIB per capita do IBGE
Fonte: API do IBGE - https://servicodados.ibge.gov.br/api/v3/

POLÍTICA: 100% DADOS REAIS
- Tenta API IBGE (3 endpoints)
- Fallback: arquivo em data/raw/pib_municipal.csv
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

# URLs da API do IBGE
IBGE_API_BASE = "https://servicodados.ibge.gov.br/api/v3"

# URLs para dados do município de Governador Valadares (código 3127701)
PIB_MUNICIPAL_URL = f"{IBGE_API_BASE}/agregados/73055/pesquisa/37/variaveis/4532?localidade=3127701"
PIB_PER_CAPITA_URL = f"{IBGE_API_BASE}/agregados/73055/pesquisa/37/variaveis/4609?localidade=3127701"

# URLs alternativas (municipios)
PIB_MUNICIPAL_URL_ALT = f"{IBGE_API_BASE}/agregados/73055/pesquisa/37/variaveis/4532?localidade=3127701&periodo=2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022"
PIB_PER_CAPITA_URL_ALT = f"{IBGE_API_BASE}/agregados/73055/pesquisa/37/variaveis/4609?localidade=3127701&periodo=2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022"

# URLs para dados de todos os municípios
PIB_MUNICIPAL_ALL_URL = f"{IBGE_API_BASE}/agregados/73055/pesquisa/37/variaveis/4532?localidade=BR"
PIB_PER_CAPITA_ALL_URL = f"{IBGE_API_BASE}/agregados/73055/pesquisa/37/variaveis/4609?localidade=BR"


def load_pib_from_raw() -> Optional[Dict]:
    """
    Carrega PIB de arquivo CSV em data/raw se disponível.
    Formato esperado: ano;valor
    """
    try:
        csv_path = DATA_DIR / "raw" / "pib_municipal.csv"
        if not csv_path.exists():
            logger.warning(f"Arquivo {csv_path} não encontrado")
            return None
            
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        logger.info(f"Carregando PIB de {csv_path}")
        
        # Transformar em formato esperado pela API
        data = {
            "localidade": {
                "id": "3127701",
                "nome": "Governador Valadares",
                "regiao": {"id": "3", "sigla": "MG", "nome": "Minas Gerais"}
            },
            "resultados": [{"series": [{"serie": {}}]}]
        }
        
        for _, row in df.iterrows():
            year = str(int(row['ano']))
            value = float(row['valor'])
            data["resultados"][0]["series"][0]["serie"][year] = value
        
        logger.info(f"PIB carregado de {csv_path}: {len(df)} registros")
        return data
        
    except Exception as e:
        logger.error(f"Erro ao carregar PIB de /raw: {e}")
        return None


def load_pib_per_capita_from_raw() -> Optional[Dict]:
    """
    Carrega PIB per capita de arquivo CSV em data/raw se disponível.
    Formato esperado: ano;valor
    """
    try:
        csv_path = DATA_DIR / "raw" / "pib_per_capita.csv"
        if not csv_path.exists():
            logger.warning(f"Arquivo {csv_path} não encontrado")
            return None
            
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        logger.info(f"Carregando PIB per capita de {csv_path}")
        
        data = {
            "localidade": {
                "id": "3127701",
                "nome": "Governador Valadares",
                "regiao": {"id": "3", "sigla": "MG", "nome": "Minas Gerais"}
            },
            "resultados": [{"series": [{"serie": {}}]}]
        }
        
        for _, row in df.iterrows():
            year = str(int(row['ano']))
            value = float(row['valor'])
            data["resultados"][0]["series"][0]["serie"][year] = value
        
        logger.info(f"PIB per capita carregado de {csv_path}: {len(df)} registros")
        return data
        
    except Exception as e:
        logger.error(f"Erro ao carregar PIB per capita de /raw: {e}")
        return None


def extrair_pib_municipal() -> Optional[Dict]:
    """
    Extrai dados do PIB municipal do IBGE.
    
    Prioridade:
    1. API IBGE (URL principal)
    2. API IBGE (URL alternativa)
    3. API IBGE (todos municípios)
    4. Arquivo local em data/raw/pib_municipal.csv
    5. Retorna None (sem dados disponíveis)
    """
    try:
        # Tenta URL principal primeiro
        response = requests.get(PIB_MUNICIPAL_URL, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                logger.info("PIB municipal obtido da API IBGE (URL principal)")
                return data[0]
        
        # Se falhar, tenta URL alternativa
        logger.warning("Tentando URL alternativa para PIB municipal")
        response = requests.get(PIB_MUNICIPAL_URL_ALT, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                logger.info("PIB municipal obtido da API IBGE (URL alternativa)")
                return data[0]
        
        # Se falhar, tenta buscar em todos os municípios
        logger.warning("Tentando buscar em todos os municípios")
        response = requests.get(PIB_MUNICIPAL_ALL_URL, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Busca pelo município específico
                for item in data:
                    if item.get("localidade", {}).get("id") == "3127701":
                        logger.info("PIB municipal encontrado na lista de todos municípios")
                        return item
        
        # Se API falhar, tenta arquivo local
        logger.warning("API IBGE não disponível, tentando arquivo local em data/raw")
        return load_pib_from_raw()
        
    except Exception as e:
        logger.error(f"Erro ao extrair PIB municipal: {e}")
        # Tenta arquivo local como último recurso
        return load_pib_from_raw()


def extrair_pib_per_capita() -> Optional[Dict]:
    """
    Extrai dados do PIB per capita do IBGE.
    
    Prioridade:
    1. API IBGE (URL principal)
    2. API IBGE (URL alternativa)
    3. API IBGE (todos municípios)
    4. Arquivo local em data/raw/pib_per_capita.csv
    5. Retorna None (sem dados disponíveis)
    """
    try:
        # Tenta URL principal primeiro
        response = requests.get(PIB_PER_CAPITA_URL, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                logger.info("PIB per capita obtido da API IBGE (URL principal)")
                return data[0]
        
        # Se falhar, tenta URL alternativa
        logger.warning("Tentando URL alternativa para PIB per capita")
        response = requests.get(PIB_PER_CAPITA_URL_ALT, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                logger.info("PIB per capita obtido da API IBGE (URL alternativa)")
                return data[0]
        
        # Se falhar, tenta buscar em todos os municípios
        logger.warning("Tentando buscar em todos os municípios")
        response = requests.get(PIB_PER_CAPITA_ALL_URL, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Busca pelo município específico
                for item in data:
                    if item.get("localidade", {}).get("id") == "3127701":
                        logger.info("PIB per capita encontrado na lista de todos municípios")
                        return item
        
        # Se API falhar, tenta arquivo local
        logger.warning("API IBGE não disponível, tentando arquivo local em data/raw")
        return load_pib_per_capita_from_raw()
        
    except Exception as e:
        logger.error(f"Erro ao extrair PIB per capita: {e}")
        # Tenta arquivo local como último recurso
        return load_pib_per_capita_from_raw()


def processar_serie_historica(dados: Dict, variavel_id: str) -> List[Dict]:
    """Processa série histórica dos dados do IBGE"""
    serie = []
    
    # Encontra as séries nos dados
    for item in dados.get("resultados", []):
        for serie_item in item.get("series", []):
            if "serie" in serie_item:
                for ano, valor in serie_item["serie"].items():
                    if valor and valor != "null":
                        try:
                            serie.append({
                                "Ano": int(ano),
                                "Valor": float(valor),
                                "Variavel": variavel_id
                            })
                        except (ValueError, TypeError):
                            continue
    
    return serie


def salvar_pib_no_banco(session, dados: List[Dict], variavel: str, nome_indicador: str):
    """Salva dados do PIB no banco de dados"""
    for item in dados:
        # Verificar se já existe para evitar violação de constraint
        existing = session.query(Indicator).filter_by(
            indicator_key=variavel,
            source="IBGE",
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
                indicator_key=variavel,
                source="IBGE",
                year=item["Ano"],
                value=item["Valor"],
                municipality_code="3127701",
                municipality_name="Governador Valadares",
                uf="MG",
                unit="R$ mil",
                collected_at=datetime.now()
            )
            session.add(indicator)
    
    session.commit()
    logger.info(f"Salvos {len(dados)} registros de {nome_indicador}")


def run_etl_pib_ibge():
    """Executa ETL completo para dados do PIB do IBGE"""
    logger.info("Iniciando ETL para dados do PIB do IBGE")
    
    session = get_session()
    
    try:
        # Extrair PIB municipal
        logger.info("Extraindo dados do PIB municipal...")
        pib_municipal = extrair_pib_municipal()
        if pib_municipal:
            serie_pib = processar_serie_historica(pib_municipal, "PIB_TOTAL")
            if serie_pib:
                salvar_pib_no_banco(session, serie_pib, "PIB_TOTAL", "PIB Municipal")
            else:
                logger.warning("Nenhum dado de PIB municipal encontrado")
        else:
            logger.error(
                "Falha ao extrair dados do PIB municipal. "
                "Verifique: (1) conexão com API IBGE, (2) arquivo data/raw/pib_municipal.csv"
            )
        
        # Extrair PIB per capita
        logger.info("Extraindo dados do PIB per capita...")
        pib_per_capita = extrair_pib_per_capita()
        if pib_per_capita:
            serie_pib_pc = processar_serie_historica(pib_per_capita, "PIB_PER_CAPITA")
            if serie_pib_pc:
                salvar_pib_no_banco(session, serie_pib_pc, "PIB_PER_CAPITA", "PIB Per Capita")
            else:
                logger.warning("Nenhum dado de PIB per capita encontrado")
        else:
            logger.error(
                "Falha ao extrair dados do PIB per capita. "
                "Verifique: (1) conexão com API IBGE, (2) arquivo data/raw/pib_per_capita.csv"
            )
        
        session.commit()
        logger.info("ETL para dados do PIB do IBGE concluído com sucesso")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Erro no ETL do PIB IBGE: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
    run_etl_pib_ibge()
