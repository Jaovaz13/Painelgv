"""
Índice Sintético de Desenvolvimento Municipal (ISDM).

Importante:
- 100% baseado em séries reais do banco (não usa benchmarks inventados).
- O score (0-1) é normalizado com base na faixa observada do próprio município
  para cada indicador, no conjunto de anos disponíveis.
- O ISDM é um índice interno para monitoramento relativo ao histórico local.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Any

import pandas as pd

from database import get_timeseries
from config import MUNICIPIO, UF

logger = logging.getLogger(__name__)

# Pesos de cada componente (soma = 1.0)
PESOS: dict[str, float] = {
    "PIB_PER_CAPITA": 0.25,
    "EMPREGOS_RAIS": 0.20,
    "IDEB_ANOS_INICIAIS": 0.20,
    "MORTALIDADE_INFANTIL": 0.20,  # invertido: menor é melhor
    "IDSC_GERAL": 0.15,
}


def _normalizar_0_1(valor: float, minimo: float, maximo: float, inverso: bool = False) -> float:
    """Normaliza valor entre 0 e 1 usando faixa observada (min/max)."""
    if pd.isna(valor) or pd.isna(minimo) or pd.isna(maximo):
        return 0.0
    if maximo == minimo:
        return 0.5
    score = (valor - minimo) / (maximo - minimo)
    score = float(max(0.0, min(1.0, score)))
    return 1.0 - score if inverso else score


def _get_value_for_year(df: pd.DataFrame, ano: int) -> Optional[float]:
    """Obtém o valor do indicador para um ano específico."""
    try:
        dfy = df[df["Ano"].astype(int) == int(ano)]
        if dfy.empty:
            return None
        return float(dfy.sort_values("Ano").iloc[-1]["Valor"])
    except Exception:
        return None


def calcular_isdm(ano: Optional[int] = None) -> Dict[str, Any]:
    """
    Calcula o ISDM para o ano especificado (ou último ano disponível por componente).

    Returns:
        Dict com score_total (0-1), score_percentual (0-100), componentes e metadados.
        Se não houver dados suficientes, score_total será None.
    """
    componentes: dict[str, dict[str, Any]] = {}

    # Carregar séries reais
    series: dict[str, pd.DataFrame] = {}
    for indicador in PESOS.keys():
        df = get_timeseries(indicador)
        if df is None or df.empty:
            logger.warning("ISDM: indicador %s indisponível no banco.", indicador)
            continue
        df = df.dropna(subset=["Ano", "Valor"]).sort_values("Ano")
        if df.empty:
            continue
        series[indicador] = df

    if not series:
        return {"score_total": None, "componentes": {}, "ano": ano, "municipio": f"{MUNICIPIO}/{UF}"}

    # Determinar ano alvo: se não especificado, usar o ano mais recente comum possível
    if ano is None:
        anos_disponiveis = None
        for df in series.values():
            yrs = set(df["Ano"].astype(int).tolist())
            anos_disponiveis = yrs if anos_disponiveis is None else anos_disponiveis.intersection(yrs)
        if anos_disponiveis:
            ano = max(anos_disponiveis)
        else:
            # fallback: usa ano mais recente entre todos
            ano = max(int(df["Ano"].max()) for df in series.values())

    # Pré-calcular min/max observados por componente no município
    ranges: dict[str, tuple[float, float]] = {}
    for indicador, df in series.items():
        ranges[indicador] = (float(df["Valor"].min()), float(df["Valor"].max()))

    # Calcular score por componente, reponderando caso falte algum
    contribs = []
    peso_total = 0.0
    for indicador, peso in PESOS.items():
        if indicador not in series:
            continue
        df = series[indicador]
        valor = _get_value_for_year(df, ano)
        if valor is None:
            logger.warning("ISDM: sem dados de %s para o ano %s.", indicador, ano)
            continue

        minimo, maximo = ranges[indicador]
        inverso = indicador == "MORTALIDADE_INFANTIL"
        score_norm = _normalizar_0_1(valor, minimo, maximo, inverso=inverso)
        contrib = score_norm * peso
        componentes[indicador] = {
            "valor_bruto": valor,
            "min_observado": minimo,
            "max_observado": maximo,
            "score_normalizado": score_norm,
            "peso": peso,
            "contribuicao": contrib,
        }
        contribs.append(contrib)
        peso_total += peso

    if not componentes or peso_total == 0:
        return {"score_total": None, "componentes": {}, "ano": ano, "municipio": f"{MUNICIPIO}/{UF}"}

    score_total = sum(contribs) / peso_total
    return {
        "score_total": round(float(score_total), 4),
        "score_percentual": round(float(score_total) * 100, 1),
        "componentes": componentes,
        "componentes_usados": len(componentes),
        "ano": int(ano),
        "municipio": f"{MUNICIPIO}/{UF}",
    }


def get_isdm_historico() -> pd.DataFrame:
    """
    Retorna série histórica do ISDM para anos onde houver dados suficientes.
    """
    # coletar anos disponíveis (união)
    anos: set[int] = set()
    for indicador in PESOS.keys():
        df = get_timeseries(indicador)
        if df is None or df.empty or "Ano" not in df.columns:
            continue
        anos.update(pd.to_numeric(df["Ano"], errors="coerce").dropna().astype(int).tolist())

    if not anos:
        return pd.DataFrame()

    registros = []
    for ano in sorted(anos):
        res = calcular_isdm(ano)
        if res.get("score_total") is None:
            continue
        registros.append(
            {"Ano": int(ano), "Valor": float(res["score_total"]), "Unidade": "Score (0-1)"}
        )

    return pd.DataFrame(registros)

