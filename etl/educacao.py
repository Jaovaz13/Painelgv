import logging
import pandas as pd
import requests
from config import COD_IBGE
from database import upsert_indicators

logger = logging.getLogger(__name__)

def ideb_municipal(cod_mun: str) -> pd.DataFrame:
    """
    Consulta IDEB via API INEP (dadosabertos.inep.gov.br).
    """
    resource_id = "8e3a4d0b-9f6a-4f5c-bb78-1f70f1e20b12" # ID Recurso Exemplo
    # Nota: ID pode mudar. Usando o fornecido.
    
    url = (
        "https://dadosabertos.inep.gov.br/api/3/action/datastore_search"
        f"?resource_id={resource_id}"
        f"&filters={{\"codigo_municipio\":\"{cod_mun}\"}}"
    )
    
    logger.info(f"Consultando IDEB INEP para {cod_mun}")
    try:
        resp = requests.get(url, timeout=60, verify=False)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("success"):
            logger.warning("API INEP retornou failure.")
            return pd.DataFrame()
            
        return pd.DataFrame(data["result"]["records"])
    except Exception as e:
        logger.error(f"Erro ao consultar INEP: {e}")
        return pd.DataFrame()

def transform_ideb(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    
    df.columns = [c.lower() for c in df.columns]
    
    # Colunas esperadas variam. Buscar 'ano' e 'ideb'
    year_col = next((c for c in df.columns if "ano" in c), None)
    val_col = next((c for c in df.columns if "ideb" in c or "nota" in c), None)
    
    if not year_col or not val_col:
        logger.warning(f"Colunas IDEB não paradas. Disp: {df.columns.tolist()}")
        return pd.DataFrame()
    
    # Converter ano e valor
    # Pode haver multiplos registros por ano (rede pub/priv/ciclo). Tirar media.
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    
    grouped = df.groupby(year_col)[val_col].mean().reset_index()
    grouped.rename(columns={year_col: "year", val_col: "value"}, inplace=True)
    grouped["unit"] = "Nota (0-10)"
    
    return grouped

def run_ideb() -> int:
    raw = ideb_municipal(COD_IBGE)
    df = transform_ideb(raw)
    if not df.empty:
        return upsert_indicators(df, indicator_key="IDEB_MEDIO", source="INEP")
    return 0

# ------------------------------------------------------------------------------
# 2. Matrículas (IBGE)
# ------------------------------------------------------------------------------

def extract_matriculas() -> pd.DataFrame:
    # Tabela 305: Matrículas
    url = f"https://apisidra.ibge.gov.br/values/t/305/n6/{COD_IBGE}"
    logger.info("Coletando Matrículas IBGE: %s", url)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        j = resp.json()
        if len(j) < 2: return pd.DataFrame()
        return pd.DataFrame(j[1:], columns=j[0])
    except Exception as e:
        logger.error("Erro API Matrículas: %s", e)
        return pd.DataFrame()

def run_matriculas() -> int:
    raw = extract_matriculas()
    if raw.empty: return 0
    
    # Transforma usando lógica similar ao PIB (D2N -> Year, V -> Value)
    col_map = {}
    for col in raw.columns:
        if col == "D2N" or "ano" in col.lower(): col_map[col] = "year"
        if col == "V" or "valor" in col.lower(): col_map[col] = "value"
        
    df = raw.rename(columns=col_map)
    df["unit"] = "Alunos"
    
    # Limpeza
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["year", "value"])
    
    return upsert_indicators(df, indicator_key="MATRICULAS_TOTAL", source="IBGE")

# ------------------------------------------------------------------------------
# Runner
# ------------------------------------------------------------------------------

def run() -> None:
    logger.info("--- Iniciando ETL Educação ---")
    run_ideb()
    run_matriculas()
    logger.info("--- Fim ETL Educação ---")
