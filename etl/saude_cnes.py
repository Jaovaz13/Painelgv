"""
ETL para indicadores hospitalares: leitos hospitalares.

Fonte (prioritária): CNES/DataSUS (se disponível via API).
Fallback obrigatório: data/raw/saude_leitos.csv

Política:
- 100% dados reais (não gera dados simulados)
- Anos dinâmicos (usa anos presentes nos dados)
- Tratamento de exceções e logs estruturados
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from config import COD_IBGE, DATA_DIR
from database import upsert_indicators
from utils.network import safe_request

logger = logging.getLogger(__name__)

CNES_API_BASE = "https://apidadosabertos.saude.gov.br/cnes"


def fetch_leitos_cnes(cod_mun: str = str(COD_IBGE)) -> Optional[pd.DataFrame]:
    """
    Busca dados de leitos via API pública CNES (quando disponível).

    Retorna DataFrame bruto (sem garantir colunas).
    """
    url = f"{CNES_API_BASE}/leitos?municipio_codigo={cod_mun}&limit=500"
    data = safe_request(url, timeout=30)
    if not data:
        logger.warning("API CNES de leitos não respondeu.")
        return None

    records = None
    if isinstance(data, dict):
        records = data.get("registros") or data.get("data") or data.get("items")
    if records is None and isinstance(data, list):
        records = data
    if not records:
        return None

    df = pd.DataFrame(records)
    logger.info("CNES leitos: %s registros brutos obtidos", len(df))
    return df


def load_leitos_from_raw() -> Optional[pd.DataFrame]:
    """
    Carrega leitos de CSV local (fallback).

    Formato esperado (delimitador ';'):
    - ano;leitos
    """
    csv_path = DATA_DIR / "raw" / "saude_leitos.csv"
    if not csv_path.exists():
        logger.warning("Arquivo %s não encontrado.", csv_path)
        return None
    try:
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
        logger.info("Leitos carregados de %s: %s registros", csv_path, len(df))
        return df
    except Exception as e:
        logger.error("Erro ao ler %s: %s", csv_path, e)
        return None


def transform_leitos(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza dados de leitos para o formato do banco."""
    if df is None or df.empty:
        return pd.DataFrame()

    data = df.copy()
    data.columns = [c.lower().strip() for c in data.columns]

    col_year = next((c for c in data.columns if c in {"ano", "year"}), None)
    col_comp = next((c for c in data.columns if "compet" in c), None)  # ex.: competencia YYYYMM
    col_value = next((c for c in data.columns if "leito" in c or "cama" in c), None)

    if col_value is None:
        # fallback: primeira coluna numérica
        num_cols = data.select_dtypes(include=["number"]).columns.tolist()
        col_value = num_cols[0] if num_cols else None

    if col_year is None and col_comp is not None:
        # Derivar year de competencia (YYYYMM)
        data["year"] = pd.to_numeric(data[col_comp].astype(str).str.slice(0, 4), errors="coerce")
        col_year = "year"

    if col_year is None or col_value is None:
        logger.error(
            "Colunas esperadas não encontradas para leitos. Disponíveis: %s",
            data.columns.tolist(),
        )
        return pd.DataFrame()

    data = data.rename(columns={col_year: "year", col_value: "value"})
    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["year", "value"])
    data["year"] = data["year"].astype(int)

    grouped = data.groupby("year", as_index=False)["value"].sum()
    grouped["unit"] = "Leitos"
    return grouped[["year", "value", "unit"]]


def run() -> None:
    """Executa ETL de leitos hospitalares (CNES/DataSUS)."""
    logger.info("Iniciando ETL Saúde – Leitos Hospitalares (CNES)")

    df_raw = fetch_leitos_cnes()
    if df_raw is None or df_raw.empty:
        logger.warning("API CNES falhou, tentando fallback raw.")
        df_raw = load_leitos_from_raw()

    if df_raw is None or df_raw.empty:
        logger.error(
            "ETL de Leitos abortado. Forneça data/raw/saude_leitos.csv "
            "com colunas: ano;leitos"
        )
        return

    df = transform_leitos(df_raw)
    if df.empty:
        logger.error("Transformação de leitos retornou DataFrame vazio.")
        return

    upsert_indicators(
        df,
        indicator_key="LEITOS_HOSPITALARES",
        source="CNES",
        category="Saúde",
    )
    logger.info("ETL Leitos concluído: %s registros salvos.", len(df))

