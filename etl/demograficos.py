"""
ETL para indicadores demográficos do IBGE:
- População (Censo 2022 - Tabela 4714)
- IDH-M (Atlas Brasil / dados.gov.br)
- Índice de GINI

Estes indicadores são fundamentais para contextualizar qualquer análise socioeconômica,
pois fornecem a base populacional e os índices de desenvolvimento e desigualdade.
"""
import logging
from pathlib import Path
import pandas as pd
from config import COD_IBGE, MUNICIPIO, DATA_DIR
from database import upsert_indicators
from utils.network import safe_request

logger = logging.getLogger(__name__)

METADATA = {
    "fonte": "IBGE / Atlas Brasil",
    "periodicidade": "Decenal (Censo)",
    "descricao": "Indicadores demográficos essenciais para análise socioeconômica"
}

RAW_DIR = DATA_DIR / "raw"

# ------------------------------------------------------------------------------
# POPULAÇÃO
# ------------------------------------------------------------------------------
def get_populacao() -> pd.DataFrame:
    """
    Obtém população do município via IBGE SIDRA.
    Tabela 4714: População residente (Censo 2022)
    """
    # Tabela 4714 - Var 93 (População residente)
    url = f"https://apisidra.ibge.gov.br/values/t/4714/v/93/p/all/n6/{COD_IBGE}?formato=json"
    
    logger.info(f"Consultando população para {COD_IBGE}")
    
    data = safe_request(url)
    if not data or len(data) < 2:
        # Fallback: Tabela mais antiga 6579
        url = f"https://apisidra.ibge.gov.br/values/t/6579/v/9324/p/all/n6/{COD_IBGE}?formato=json"
        data = safe_request(url)
        
    if not data or len(data) < 2:
        logger.warning("Dados de população não encontrados via API.")
        return pd.DataFrame()
    
    df = pd.DataFrame(data[1:])
    
    # Colunas SIDRA: D2N (Período), V (Valor)
    col_val = "V" if "V" in df.columns else df.columns[-1]
    col_ano = "D2N" if "D2N" in df.columns else "Ano"
    
    df["value"] = pd.to_numeric(df[col_val], errors="coerce")
    df["year"] = df[col_ano].astype(str).str[:4].astype(int)
    df["unit"] = "Habitantes"
    
    return df[["year", "value", "unit"]].dropna()


# ------------------------------------------------------------------------------
# IDH-M (Índice de Desenvolvimento Humano Municipal)
# Fonte: Atlas Brasil - Dados históricos em CSV
# ------------------------------------------------------------------------------
def get_idhm() -> pd.DataFrame:
    """
    Carrega IDH-M do município a partir do CSV em data/raw/idhm.csv.
    Formato esperado: ano;valor;fonte
    """
    csv_path = RAW_DIR / "idhm.csv"
    if not csv_path.exists():
        logger.warning(f"Arquivo {csv_path} não encontrado.")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
        df.columns = [c.lower().strip() for c in df.columns]
        df = df.rename(columns={"ano": "year", "valor": "value"})
        df["unit"] = "Índice"
        return df[["year", "value", "unit"]].dropna()
    except Exception as e:
        logger.exception(f"Erro ao ler idhm.csv: {e}")
        return pd.DataFrame()


# ------------------------------------------------------------------------------
# ÍNDICE DE GINI
# Mede a desigualdade de renda (0 = igualdade, 1 = desigualdade máxima)
# Fonte: IBGE/Censos - Dados históricos em CSV
# ------------------------------------------------------------------------------
def get_gini() -> pd.DataFrame:
    """
    Carrega Índice de Gini do município a partir do CSV em data/raw/gini.csv.
    Formato esperado: ano;valor;fonte
    """
    csv_path = RAW_DIR / "gini.csv"
    if not csv_path.exists():
        logger.warning(f"Arquivo {csv_path} não encontrado.")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
        df.columns = [c.lower().strip() for c in df.columns]
        df = df.rename(columns={"ano": "year", "valor": "value"})
        df["unit"] = "Índice"
        return df[["year", "value", "unit"]].dropna()
    except Exception as e:
        logger.exception(f"Erro ao ler gini.csv: {e}")
        return pd.DataFrame()


def run() -> None:
    """Executa ETL de indicadores demográficos."""
    logger.info("--- Iniciando ETL Demográficos ---")
    
    # População
    df_pop = get_populacao()
    if not df_pop.empty:
        upsert_indicators(df_pop, indicator_key="POPULACAO", source="IBGE", category="Demografia")
        logger.info(f"População: {len(df_pop)} registros")
    
    # IDH-M
    df_idhm = get_idhm()
    if not df_idhm.empty:
        upsert_indicators(df_idhm, indicator_key="IDHM", source="ATLAS_BRASIL", category="Desenvolvimento")
        logger.info(f"IDH-M: {len(df_idhm)} registros")
    else:
        logger.warning("IDH-M não carregado. Verifique data/raw/idhm.csv")
    
    # GINI
    df_gini = get_gini()
    if not df_gini.empty:
        upsert_indicators(df_gini, indicator_key="GINI", source="IBGE", category="Desigualdade")
        logger.info(f"GINI: {len(df_gini)} registros")
    else:
        logger.warning("GINI não carregado. Verifique data/raw/gini.csv")
    
    logger.info("--- Fim ETL Demográficos ---")

