import logging
from pathlib import Path

import pandas as pd

from config import DATA_DIR
from database import upsert_indicators


logger = logging.getLogger(__name__)


def load_iss(path: Path) -> pd.DataFrame:
    logger.info("Carregando ISS de %s", path)
    return pd.read_excel(path)


def transform_iss(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exemplo: receita de ISS por ano.
    Ajuste mapeamento conforme layout real da planilha da fazenda municipal.
    """
    if df.empty:
        return pd.DataFrame(columns=["year", "value", "unit"])

    col_map = {}
    for col in df.columns:
        if col.lower().startswith("ano"):
            col_map[col] = "ano"
        if "iss" in col.lower() or "receita" in col.lower():
            col_map[col] = "receita_iss"
    df = df.rename(columns=col_map)

    if "ano" not in df.columns or "receita_iss" not in df.columns:
        logger.warning(
            "Layout inesperado da planilha de ISS. Colunas: %s", df.columns.tolist()
        )
        return pd.DataFrame(columns=["year", "value", "unit"])

    grouped = df.groupby("ano", as_index=False)["receita_iss"].sum()
    grouped.rename(columns={"ano": "year", "receita_iss": "value"}, inplace=True)
    grouped["unit"] = "R$"
    return grouped


def run():
    """
    Executa ETL de ISS da fazenda municipal a partir de planilha local.
    """
    logger.info("Iniciando ETL Fazenda Municipal (ISS)")
    raw_dir = DATA_DIR / "raw"
    files = [f for f in os.listdir(raw_dir) if "iss" in f.lower() or "fazenda" in f.lower()]

    if not files:
        logger.warning("Nenhum arquivo de ISS encontrado em data/raw")
        return pd.DataFrame()

    path_file = raw_dir / files[0]
    df_raw = load_iss(path_file)
    df = transform_iss(df_raw)
    
    if not df.empty:
        upsert_indicators(df, indicator_key="RECEITA_ISS", source="FAZENDA_MUN", category="Capacidade Fiscal")
        logger.info("ETL Fazenda Municipal concluído.")
    
    return df
