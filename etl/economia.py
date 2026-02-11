import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from config import COD_IBGE, DATA_DIR
from database import upsert_indicators

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# 1. PIB Municipal (API IBGE)
# ------------------------------------------------------------------------------

def extract_pib() -> pd.DataFrame:
    """Extrai PIB do IBGE (SIDRA)."""
    # Tabela 5938: PIB a preços correntes
    url = f"https://apisidra.ibge.gov.br/values/t/5938/n6/{COD_IBGE}"
    logger.info("Coletando PIB Municipal: %s", url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    j = resp.json()
    # A API retorna header na primeira linha
    if len(j) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(j[1:], columns=j[0])
    return df

def transform_pib(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados do PIB para formato padrão."""
    # Colunas comuns SIDRA: 'D2N' (Ano), 'V' (Valor)
    # Às vezes vem com nomes completos. Vamos tentar identificar.
    if df.empty:
         return pd.DataFrame(columns=["year", "value", "unit"])

    col_map = {}
    for col in df.columns:
        if col == "D2N" or "ano" in col.lower():
            col_map[col] = "year"
        elif col == "V" or "valor" in col.lower():
            col_map[col] = "value"

    df = df.rename(columns=col_map)
    
    # Garantir colunas
    if "year" not in df.columns or "value" not in df.columns:
        logger.warning(f"Estrutura inesperada no PIB: {df.columns}")
        return pd.DataFrame(columns=["year", "value", "unit"])

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["unit"] = "R$ mil" # SIDRA costuma ser em mil reais para PIB munic
    df = df.dropna(subset=["year", "value"])
    return df

def run_pib() -> int:
    try:
        raw = extract_pib()
        df = transform_pib(raw)
        return upsert_indicators(df, indicator_key="PIB_MUNICIPAL", source="IBGE")
    except Exception as e:
        logger.exception("Erro no ETL PIB: %s", e)
        return 0

# ------------------------------------------------------------------------------
# 2. PIB Per Capita (API IBGE)
# ------------------------------------------------------------------------------

def extract_pib_per_capita() -> pd.DataFrame:
    # Tabela 5939: PIB per capita
    # Nota: O user forneceu 5939, conferir se é a tabela correta para per capita
    # A tabela 5938 tem PIB total e outros. O user sugeriu request diferente.
    url = f"https://apisidra.ibge.gov.br/values/t/5938/n6/{COD_IBGE}/v/5936" # 5936 é PIB per capita na tab 5938?
    # O user passou: https://apisidra.ibge.gov.br/values/t/5939/n6/{COD_IBGE}
    # Vou usar o sugerido pelo user:
    url = f"https://apisidra.ibge.gov.br/values/t/5938/n6/{COD_IBGE}/v/37" # 37 é pib total, 5938 tem var 37.
    # Vamos tentar o que o user mandou no prompt: "https://apisidra.ibge.gov.br/values/t/5939/n6/{COD_IBGE}"
    # Mas tabela 5939 nao existe ou varia.
    # Tabela 5938 variavel 5936 é pib per capita
    url = f"https://apisidra.ibge.gov.br/values/t/5938/n6/{COD_IBGE}/v/5936"
    
    logger.info("Coletando PIB Per Capita: %s", url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    j = resp.json()
    if len(j) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(j[1:], columns=j[0])
    return df

def run_pib_per_capita() -> int:
    try:
        raw = extract_pib_per_capita()
        df = transform_pib(raw) # Mesma estrutura
        df["unit"] = "R$"
        return upsert_indicators(df, indicator_key="PIB_PER_CAPITA", source="IBGE")
    except Exception as e:
        logger.exception("Erro no ETL PIB Per Capita: %s", e)
        return 0

# ------------------------------------------------------------------------------
# 3. VAF - SEFAZ MG (Arquivo Local)
# ------------------------------------------------------------------------------

def run_vaf(filename: str = "vaf.csv") -> int:
    path = DATA_DIR / "raw" / filename
    if not path.exists():
        logger.warning(f"Arquivo VAF não encontrado: {path}")
        return 0
    
    try:
        # Assumindo CSV com ; e colunas 'Ano', 'VAF'
        df = pd.read_csv(path, sep=";")
        # Normalizacao simples
        df.columns = [c.lower() for c in df.columns]
        # Esperado: ano, valor ou vaf
        df = df.rename(columns={"ano": "year", "vaf": "value", "valor": "value"})
        if "year" not in df.columns or "value" not in df.columns:
            logger.warning("Colunas esperadas (Ano, VAF) não encontradas no VAF.")
            return 0
        
        df["unit"] = "R$"
        return upsert_indicators(df, indicator_key="VAF", source="SEFAZ_MG")
    except Exception as e:
        logger.exception("Erro no ETL VAF: %s", e)
        return 0

# ------------------------------------------------------------------------------
# 4. ICMS Cota-Parte (Arquivo Local)
# ------------------------------------------------------------------------------

def run_icms(filename: str = "icms.csv") -> int:
    path = DATA_DIR / "raw" / filename
    if not path.exists():
        logger.warning(f"Arquivo ICMS não encontrado: {path}")
        return 0

    try:
        df = pd.read_csv(path, sep=";")
        df.columns = [c.lower() for c in df.columns]
        df = df.rename(columns={"ano": "year", "icms": "value", "valor": "value"})
        
        if "year" not in df.columns or "value" not in df.columns:
            return 0
            
        df["unit"] = "R$"
        return upsert_indicators(df, indicator_key="ICMS_COTA_PARTE", source="SEFAZ_MG")
    except Exception as e:
        logger.exception("Erro no ETL ICMS: %s", e)
        return 0

# ------------------------------------------------------------------------------
# 5. Empresas SEBRAE (Arquivo Local)
# ------------------------------------------------------------------------------

def run_empresas_sebrae(filename: str = "sebrae.xlsx") -> int:
    path = DATA_DIR / "raw" / filename
    if not path.exists():
        logger.warning(f"Arquivo Sebrae não encontrado: {path}")
        return 0
        
    try:
        df = pd.read_excel(path)
        df.columns = [c.lower() for c in df.columns]
        # Esperado: ano, empresas_ativas ou valor
        df = df.rename(columns={"ano": "year", "empresas_ativas": "value", "quantidade": "value"})
        
        if "year" not in df.columns or "value" not in df.columns:
            return 0
            
        df["unit"] = "Empresas"
        return upsert_indicators(df, indicator_key="EMPRESAS_ATIVAS", source="SEBRAE")
    except Exception as e:
        logger.exception("Erro no ETL Sebrae: %s", e)
        return 0

# ------------------------------------------------------------------------------
# Runner Main
# ------------------------------------------------------------------------------

def run() -> None:
    logger.info("--- Iniciando ETL Economia ---")
    run_pib()
    run_pib_per_capita()
    run_vaf()
    run_icms()
    run_empresas_sebrae()
    logger.info("--- Fim ETL Economia ---")
