import logging
from pathlib import Path
import sys
import os

import pandas as pd
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import COD_IBGE, DATA_DIR
from database import upsert_indicators

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# 1. Emprego Formal (CAGED)
# ------------------------------------------------------------------------------

def extract_caged(ano: int) -> pd.DataFrame:
    url = f"https://dadosabertos.mte.gov.br/api/caged/municipio/{COD_IBGE}/{ano}"
    logger.info("Coletando CAGED para %s (Ano: %s)", COD_IBGE, ano)
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return pd.DataFrame(resp.json())
    except Exception as e:
        logger.error("Erro na API do CAGED para %s: %s", ano, e)
        return pd.DataFrame()

def transform_caged(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["year", "value", "unit"])
    
    # API do CAGED geralmente retorna colunas como 'competencia' (ex: 202401), 'saldo_movimentacao', etc.
    # Mas o layout exato pode variar. Vamos tentar identificar saldo.
    col_map = {}
    for col in df.columns:
        if "saldo" in col.lower():
            col_map[col] = "saldo"
    
    df = df.rename(columns=col_map)
    if "saldo" not in df.columns:
        logger.warning(f"Coluna de saldo não encontrada no CAGED. Cols: {df.columns}")
        return pd.DataFrame(columns=["year", "value", "unit"])
    
    # Se tiver mês/competência, idealmente somamos o saldo do ano.
    # Se o DF veio da url /municipio/{cod}/{ano}, assume-se que são dados daquele ano.
    # Vamos somar o saldo.
    saldo_ano = pd.to_numeric(df["saldo"], errors="coerce").sum()
    
    # Como não temos o ano no DF necessariamente se a API não retornar,
    # vamos ter que confiar no ano passado na extração?
    # O transform precisa do ano para montar o DF final.
    # Mas o transform aqui recebe só o DF.
    # Vamos tentar achar coluna de ano/competencia.
    val_ano = None
    for col in df.columns:
        if "ano" in col.lower() or "competencia" in col.lower():
            # Tentar extrair ano
            try:
                # Pegar o primeiro valor válido
                val = str(df[col].iloc[0])
                if len(val) >= 4:
                    val_ano = int(val[:4])
                    break
            except:
                pass
    
    if val_ano is None:
        # Se não achou, retorna dataframe vazio pois não sabemos o ano
        # Ou fazemos o extract já retornar com ano?
        # Vamos assumir que o caller sabe o ano ou que o DF tem dados.
        # Fallback: se não achou ano, não consegue criar registro.
        return pd.DataFrame(columns=["year", "value", "unit"])

    return pd.DataFrame([{
        "year": val_ano,
        "value": saldo_ano,
        "unit": "Vagas (Saldo)"
    }])

def run_caged(anos: list[int]) -> None:
    for ano in anos:
        raw = extract_caged(ano)
        if raw.empty:
            continue
            
        # Hack: se o transform não conseguir achar o ano, ele falha.
        # Mas o extract sabe o ano. Vamos injetar o ano no raw se não tiver.
        if "ano" not in [c.lower() for c in raw.columns]:
            raw["ano"] = ano
            
        df = transform_caged(raw)
        upsert_indicators(df, indicator_key="EMPREGOS_CAGED", source="CAGED")

# ------------------------------------------------------------------------------
# 2. Massa Salarial (RAIS) - Arquivo Local
# ------------------------------------------------------------------------------

def run_rais(filename: str = "rais.csv") -> int:
    path = DATA_DIR / "raw" / filename
    if not path.exists():
        logger.warning(f"Arquivo RAIS não encontrado: {path}")
        return 0

    try:
        df = pd.read_csv(path, sep=";", encoding="latin1")
        df.columns = [c.lower() for c in df.columns]
        
        # Esperado: ano, valor/massa
        col_map = {}
        for col in df.columns:
            if "ano" in col: col_map[col] = "year"
            if "massa" in col or "valor" in col: col_map[col] = "value"
            
        df = df.rename(columns=col_map)
        
        if "year" not in df.columns or "value" not in df.columns:
            return 0
            
        df["unit"] = "R$"
        return upsert_indicators(df, indicator_key="MASSA_SALARIAL", source="RAIS")
    except Exception as e:
        logger.exception("Erro no ETL RAIS: %s", e)
        return 0

# ------------------------------------------------------------------------------
# Runner
# ------------------------------------------------------------------------------

def run() -> None:
    logger.info("--- Iniciando ETL Trabalho e Renda ---")
    run_caged(range(2020, 2025)) 
    run_rais()
    logger.info("--- Fim ETL Trabalho e Renda ---")
