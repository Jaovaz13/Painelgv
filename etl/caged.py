import logging
import pandas as pd
import requests
from typing import Optional

from config import COD_IBGE
from database import upsert_indicators
from utils.network import safe_request

METADATA = {
    "fonte": "CAGED - Novo",
    "periodicidade": "Mensal",
    "ultima_atualizacao": "Automática"
}

logger = logging.getLogger(__name__)

def caged_saldo(cod_mun: str) -> pd.DataFrame:
    """
    Consulta o saldo do CAGED via API CKAN.
    """
    # ID do recurso (pode mudar, ideal seria busca dinâmica)
    resource_id = "caged-novo" # Placeholder, usar ID real se souber ou manter lógica de busca
    
    # URL de busca no datastore
    url = (
        "http://dados.mte.gov.br/api/3/action/datastore_search"
        f"?resource_id={resource_id}&q={cod_mun}&limit=5000"
    )
    
    logger.info(f"Consultando CAGED CKAN para {cod_mun}")
    
    data = safe_request(url, timeout=60)
    
    if not data or not data.get("success"):
        logger.warning("API CAGED retornou falha ou vazio")
        return pd.DataFrame()
        
    records = data.get("result", {}).get("records", [])
    return pd.DataFrame(records)

def transform_caged(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza dados do CAGED.
    Espera colunas como 'competenciamov', 'saldomovimentacao', etc.
    """
    if df.empty:
        return pd.DataFrame()

    # Normalizar nomes de colunas para minúsculo
    df.columns = [c.lower() for c in df.columns]
    
    # Mapear colunas
    # Exemplo CKAN: 'competenciamov' (YYYYMM), 'saldomovimentacao'
    if "competenciamov" not in df.columns or "saldomovimentacao" not in df.columns:
        logger.warning(f"Colunas esperadas do CAGED não encontradas. Disponíveis: {df.columns.tolist()}")
        return pd.DataFrame()

    # Converter competência para Ano (ou manter mensal se o banco suportar, aqui vamos agregar anual)
    df["competenciamov"] = df["competenciamov"].astype(str)
    df["year"] = df["competenciamov"].str[:4].astype(int)
    df["saldomovimentacao"] = pd.to_numeric(df["saldomovimentacao"], errors="coerce").fillna(0)
    
    # Agrupar por ano
    grouped = df.groupby("year")["saldomovimentacao"].sum().reset_index()
    grouped.rename(columns={"saldomovimentacao": "value"}, inplace=True)
    grouped["unit"] = "Vagas (Saldo)"
    
    return grouped

def run() -> None:
    logger.info("Iniciando ETL CAGED (CKAN API).")
    raw = caged_saldo(COD_IBGE)
    df = transform_caged(raw)
    
    if not df.empty:
        inserted = upsert_indicators(df, indicator_key="EMPREGOS_CAGED", source="CAGED_NOVO")
        logger.info(f"ETL CAGED concluído. Registros novos/atualizados: {inserted}")
    else:
        logger.warning("Nenhum dado do CAGED foi processado.")

