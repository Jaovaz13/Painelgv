import logging
import pandas as pd
from pathlib import Path

import sys
import os
import importlib.util
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT in sys.path:
    sys.path.remove(_PROJECT_ROOT)
sys.path.insert(0, _PROJECT_ROOT)

# Evitar colisão com módulos chamados "utils" (ex.: etl/utils.py ou pacotes terceiros)
if "utils" in sys.modules:
    del sys.modules["utils"]

from config import DATA_DIR, COD_IBGE, MUNICIPIO
from database import upsert_indicators
try:
    from utils.convert_xlsx import prioritize_xlsx_if_exists
except Exception:
    _convert_path = os.path.join(_PROJECT_ROOT, "utils", "convert_xlsx.py")
    _spec = importlib.util.spec_from_file_location("painel_gv_convert_xlsx", _convert_path)
    _mod = importlib.util.module_from_spec(_spec)
    assert _spec and _spec.loader
    _spec.loader.exec_module(_mod)
    prioritize_xlsx_if_exists = _mod.prioritize_xlsx_if_exists

logger = logging.getLogger(__name__)

METADATA = {
    "fonte": "Manual (CSV)",
    "periodicidade": "Variável",
    "ultima_atualizacao": "Manual"
}

def load_csv_generic(filename: str, sep: str = ";", encoding: str = "utf-8") -> pd.DataFrame:
    path = DATA_DIR / "raw" / filename
    if not path.exists():
        logger.warning(f"Arquivo manual não encontrado: {path}")
        return pd.DataFrame()
    try:
        return pd.read_csv(path, sep=sep, encoding=encoding)
    except Exception as e:
        logger.error(f"Erro ao ler {filename}: {e}")
        return pd.DataFrame()

# ------------------------------------------------------------------------------
# SEBRAE
# ------------------------------------------------------------------------------
def run_sebrae():
    df = load_csv_generic("sebrae.csv")
    if df.empty: return
    
    # Esperado: ano, empresas_ativas, mei, etc.
    df.columns = [c.lower() for c in df.columns]
    if "ano" not in df.columns: return

    # Empresas Ativas
    if "empresas_ativas" in df.columns:
        aux = df[["ano", "empresas_ativas"]].rename(columns={"ano": "year", "empresas_ativas": "value"})
        aux["unit"] = "Unidades"
        upsert_indicators(aux, indicator_key="EMPRESAS_ATIVAS", source="SEBRAE", category="Empreendedorismo")

    # MEI
    if "mei" in df.columns:
        aux = df[["ano", "mei"]].rename(columns={"ano": "year", "mei": "value"})
        aux["unit"] = "Unidades"
        upsert_indicators(aux, indicator_key="EMPREENDEDORES_MEI", source="SEBRAE", category="Empreendedorismo")

# ------------------------------------------------------------------------------
# MAPBIOMAS
# ------------------------------------------------------------------------------
def _read_mapbiomas_file(path):
    if str(path).lower().endswith(".csv"):
        return pd.read_csv(path, sep=None, engine="python")
    return pd.read_excel(path)

def run_mapbiomas():
    raw_dir = DATA_DIR / "raw"
    files = [f for f in raw_dir.iterdir() if "mapbiomas" in f.name.lower() and f.suffix.lower() in {".csv", ".xlsx", ".xls"}]
    if not files:
        return

    cols_map = {
        "area_urbana": "AREA_URBANA",
        "vegetacao_nativa": "VEGETACAO_NATIVA",
        "uso_agropecuario": "USO_AGROPECUARIO",
    }

    for path in files:
        # Priorizar XLSX se existir
        if path.suffix.lower() == ".csv":
            xlsx_path = prioritize_xlsx_if_exists(f"*{path.stem}*")
            if xlsx_path and xlsx_path.exists():
                continue  # será processado como XLSX
        df = _read_mapbiomas_file(path)
        if df.empty:
            continue

        df.columns = [c.strip().lower() for c in df.columns]

        # Filtrar município se existir coluna
        municipio_col = next((c for c in df.columns if "municip" in c), None)
        cod_col = next((c for c in df.columns if "ibge" in c or "codigo" in c), None)
        if cod_col:
            df = df[df[cod_col].astype(str) == str(COD_IBGE)]
        elif municipio_col:
            df = df[df[municipio_col].astype(str).str.contains(MUNICIPIO, case=False, na=False)]

        if df.empty:
            continue

        year_col = "year" if "year" in df.columns else "ano" if "ano" in df.columns else None
        if year_col:
            for col, key in cols_map.items():
                if col in df.columns:
                    aux = df[[year_col, col]].rename(columns={year_col: "year", col: "value"})
                    aux["unit"] = "ha"
                    upsert_indicators(aux, indicator_key=key, source="MAPBIOMAS", category="Sustentabilidade")
            continue

        # Fallback: colunas por ano
        year_cols = [c for c in df.columns if c.isdigit() and len(c) == 4]
        class_col = next((c for c in df.columns if "classe" in c or "class" in c), None)
        if not year_cols:
            continue

        if class_col:
            melted = df[[class_col] + year_cols].melt(id_vars=[class_col], var_name="year", value_name="value")
            melted["year"] = melted["year"].astype(int)
            for col, key in cols_map.items():
                if "urbana" in col:
                    mask = melted[class_col].astype(str).str.contains("urb", case=False, na=False)
                elif "vegetacao" in col:
                    mask = melted[class_col].astype(str).str.contains("veg|floresta|nativa", case=False, na=False)
                else:
                    mask = melted[class_col].astype(str).str.contains("agro|pecu", case=False, na=False)
                aux = melted[mask].groupby("year")["value"].sum().reset_index()
                if not aux.empty:
                    aux["unit"] = "ha"
                    upsert_indicators(aux, indicator_key=key, source="MAPBIOMAS", category="Sustentabilidade")
        else:
            aux = df[year_cols].apply(pd.to_numeric, errors="coerce").sum().reset_index()
            aux.columns = ["year", "value"]
            aux["year"] = aux["year"].astype(int)
            aux["unit"] = "ha"
            upsert_indicators(aux, indicator_key="AREA_URBANA", source="MAPBIOMAS", category="Sustentabilidade")

# ------------------------------------------------------------------------------
# SEEG
# ------------------------------------------------------------------------------
def run_seeg():
    df = load_csv_generic("seeg.csv", sep=",")
    if df.empty: return
    
    df.columns = [c.lower() for c in df.columns]
    if "ano" not in df.columns and "year" not in df.columns: return
    
    col_ano = "year" if "year" in df.columns else "ano"
    col_val = "emissoes" if "emissoes" in df.columns else "value"
    
    if col_val in df.columns:
        aux = df[[col_ano, col_val]].rename(columns={col_ano: "year", col_val: "value"})
        aux["unit"] = "tCO2e"
        upsert_indicators(aux, indicator_key="EMISSOES_GEE", source="SEEG", category="Sustentabilidade")


def run() -> None:
    logger.info("Iniciando ETL Fontes Manuais.")
    run_sebrae()
    run_mapbiomas()
    run_seeg()
    logger.info("ETL Fontes Manuais concluído.")
