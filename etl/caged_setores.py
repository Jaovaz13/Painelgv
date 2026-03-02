"""
ETL para ranking de setores empregadores via CAGED por seção CNAE.

Fonte (prioritária): API pública (se disponível).
Fallback obrigatório: data/raw/caged_setores.csv

Política:
- 100% dados reais (não gera dados simulados)
- Anos dinâmicos (usa janela móvel baseada no ano atual)
- Tratamento de exceções e logs estruturados
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from config import COD_IBGE, DATA_DIR
from database import upsert_indicators
from utils.network import safe_request

logger = logging.getLogger(__name__)

# Mapeamento de seções CNAE para nomes legíveis
SECOES_CNAE: dict[str, str] = {
    "A": "Agropecuária",
    "B": "Indústrias Extrativas",
    "C": "Indústria de Transformação",
    "D": "Eletricidade e Gás",
    "E": "Água e Saneamento",
    "F": "Construção Civil",
    "G": "Comércio",
    "H": "Transporte e Armazenagem",
    "I": "Alojamento e Alimentação",
    "J": "Informação e Comunicação",
    "K": "Atividades Financeiras",
    "L": "Atividades Imobiliárias",
    "M": "Atividades Profissionais",
    "N": "Serviços Administrativos",
    "O": "Administração Pública",
    "P": "Educação",
    "Q": "Saúde e Serviços Sociais",
    "R": "Artes e Cultura",
    "S": "Outras Atividades de Serviços",
    "T": "Serviços Domésticos",
    "U": "Organismos Internacionais",
}


def fetch_caged_by_sector_api(cod_mun: str = str(COD_IBGE)) -> Optional[pd.DataFrame]:
    """
    Busca saldo CAGED por seção CNAE via API pública (se disponível).

    Retorna DataFrame com colunas mínimas que permitam transformar em:
    [secao, saldo, year].
    """
    ano_atual = datetime.now().year
    frames: list[pd.DataFrame] = []

    # Janela móvel: últimos 3 anos + ano atual
    for ano in range(ano_atual - 3, ano_atual + 1):
        url = (
            "https://api.dados.gov.br/ed/v1/mercado_trabalho/caged"
            f"?municipio={cod_mun}&ano={ano}&agrupamento=secaoatividade&limit=200"
        )
        data = safe_request(url, timeout=30)
        if not data:
            continue

        records = data.get("data", []) if isinstance(data, dict) else data
        if not records:
            continue

        df = pd.DataFrame(records)
        df["year"] = ano
        frames.append(df)

    if not frames:
        return None

    return pd.concat(frames, ignore_index=True)


def load_caged_sector_from_raw() -> Optional[pd.DataFrame]:
    """
    Carrega dados de setores do CAGED de CSV local (fallback).

    Formato esperado (delimitador ';'):
    - secao;nome_setor;saldo;ano
    """
    csv_path = DATA_DIR / "raw" / "caged_setores.csv"
    if not csv_path.exists():
        logger.warning("Arquivo %s não encontrado para fallback de setores.", csv_path)
        return None
    try:
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
        logger.info("Setores CAGED carregados de %s: %s registros", csv_path, len(df))
        return df
    except Exception as e:
        logger.error("Erro ao carregar %s: %s", csv_path, e)
        return None


def transform_sector_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza os dados de setores para o formato de agregação por seção e ano.

    Retorna DataFrame com colunas:
    - secao, year, value, unit, nome_setor
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]

    col_secao = next((c for c in df.columns if "secao" in c or "seção" in c or "section" in c), None)
    col_saldo = next((c for c in df.columns if "saldo" in c or "balance" in c), None)
    col_ano = next((c for c in df.columns if c in {"ano", "year"}), None)

    # Alguns retornos podem ter nomes diferentes
    if col_secao is None:
        col_secao = next((c for c in df.columns if "atividade" in c and "secao" in c), None)
    if col_saldo is None:
        col_saldo = next((c for c in df.columns if "mov" in c and "saldo" in c), None)

    if not all([col_secao, col_saldo, col_ano]):
        logger.error(
            "Colunas esperadas não encontradas para setores CAGED. Disponíveis: %s",
            df.columns.tolist(),
        )
        return pd.DataFrame()

    df = df.rename(columns={col_secao: "secao", col_saldo: "saldo", col_ano: "year"})
    df["saldo"] = pd.to_numeric(df["saldo"], errors="coerce").fillna(0)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    grouped = (
        df.groupby(["secao", "year"], as_index=False)["saldo"]
        .sum()
        .rename(columns={"saldo": "value"})
    )
    grouped["secao"] = grouped["secao"].astype(str).str.strip().str.upper()
    grouped["nome_setor"] = grouped["secao"].map(SECOES_CNAE).fillna("Outros")
    grouped["unit"] = "Vagas (Saldo)"
    return grouped


def run() -> None:
    """Executa ETL de ranking de setores empregadores (CAGED por CNAE)."""
    logger.info("Iniciando ETL CAGED por setor (CNAE)")

    # 1) Tentar API
    df_raw = fetch_caged_by_sector_api()

    # 2) Fallback raw
    if df_raw is None or df_raw.empty:
        logger.warning("API de setores CAGED falhou, tentando fallback raw.")
        df_raw = load_caged_sector_from_raw()

    if df_raw is None or df_raw.empty:
        logger.error(
            "ETL de setores CAGED abortado: sem dados disponíveis. "
            "Forneça data/raw/caged_setores.csv com colunas: secao;nome_setor;saldo;ano"
        )
        return

    df = transform_sector_data(df_raw)
    if df.empty:
        logger.error("Transformação dos dados de setores retornou DataFrame vazio.")
        return

    # Salvar cada seção como indicador separado
    for secao, group in df.groupby("secao"):
        secao = str(secao).upper()
        indicator_key = f"EMPREGOS_SETOR_{secao}"
        nome = str(group["nome_setor"].iloc[0])

        df_setor = group[["year", "value", "unit"]].copy()
        upsert_indicators(
            df_setor,
            indicator_key=indicator_key,
            source="CAGED_SETORES",
            category="Trabalho e Renda",
        )
        logger.info("Setor %s (%s): %s registros salvos.", nome, secao, len(df_setor))

    logger.info("ETL CAGED por setor concluído.")

