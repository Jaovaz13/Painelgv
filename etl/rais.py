import logging
from pathlib import Path

import pandas as pd

from config import DATA_DIR
from database import upsert_indicators


logger = logging.getLogger(__name__)


def load_rais_csv(path: Path) -> pd.DataFrame:
    logger.info("Carregando RAIS de %s", path)
    df = pd.read_csv(path, sep=";", encoding="latin1")
    return df


def transform_rais(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exemplo: total de empregos formais por ano.
    Ajuste mapeamento conforme layout do arquivo RAIS utilizado.
    """
    if df.empty:
        return pd.DataFrame(columns=["year", "value", "unit"])

    col_map = {}
    for col in df.columns:
        if col.lower().startswith("ano"):
            col_map[col] = "ano"
        if "vínculos" in col.lower() or "vinculos" in col.lower():
            col_map[col] = "empregos"

    df = df.rename(columns=col_map)

    if "ano" not in df.columns or "empregos" not in df.columns:
        logger.warning(
            "Layout inesperado de RAIS. Colunas disponíveis: %s", df.columns.tolist()
        )
        return pd.DataFrame(columns=["year", "value", "unit"])

    grouped = df.groupby("ano", as_index=False)["empregos"].sum()
    grouped.rename(columns={"ano": "year", "empregos": "value"}, inplace=True)
    grouped["unit"] = "empregos formais"
    return grouped


def run(path: Path | None = None) -> None:
    """
    Executa ETL RAIS a partir de um CSV local.
    """
    logger.info("Iniciando ETL RAIS.")

    if path is None:
        # Exemplo de caminho padrão. Ajuste ao seu layout real.
        path = DATA_DIR / "raw" / "rais.csv"

    if not path.exists():
        logger.warning("Arquivo RAIS não encontrado em %s. Pulando ETL RAIS.", path)
        return

    df_raw = load_rais_csv(path)
    df = transform_rais(df_raw)
    inserted = upsert_indicators(df, indicator_key="EMPREGOS_RAIS", source="RAIS")
    logger.info("ETL RAIS concluído. Registros novos: %s", inserted)

