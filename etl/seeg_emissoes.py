import pandas as pd
import logging
import os
from etl.utils import padronizar
from config import MUNICIPIO, UF, DATA_DIR, COD_IBGE
from database import upsert_indicators

logger = logging.getLogger(__name__)

def process_seeg_xls(path_file):
    """
    Processa dados de emissões do SEEG (Excel).
    Format 13.0 municipal resumido.
    """
    logger.info(f"Processando SEEG de: {path_file}")
    
    try:
        # Spreadsheet usually has 'Dados' or similar as primary data source
        df = pd.read_excel(path_file, engine='openpyxl')
        
        # Mapeamento de colunas SEEG 13.0
        cols_map = {
            "Código IBGE": "cod_ibge",
            "Ano": "ano",
            "Emissões (t CO2e)": "valor",
            "Emissões Totais (t CO2e)": "valor",
            "GWP-AR5": "valor",
            "Município": "municipio"
        }
        df = df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns})
        
        if "cod_ibge" in df.columns:
            df = df[df["cod_ibge"].astype(str) == str(COD_IBGE)]
        elif "municipio" in df.columns:
            df = df[df["municipio"].astype(str).str.contains(MUNICIPIO, case=False, na=False)]
            
        if "ano" not in df.columns or "valor" not in df.columns:
            logger.error(f"Colunas obrigatórias não encontradas no SEEG Excel. Colunas: {df.columns}")
            return pd.DataFrame()
            
        df = df[["ano", "valor"]].groupby("ano").sum().reset_index()
        df["mes"] = 0
        
        return padronizar(
            df,
            indicador="Emissões de GEE (tCO2e)",
            categoria="Sustentabilidade",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="SEEG (Observatório do Clima)",
            manual=False
        )
    except Exception as e:
        logger.error(f"Erro ao processar SEEG Excel: {e}")
        return pd.DataFrame()

def process_seeg_csv(path_file: str) -> pd.DataFrame:
    """
    Processa CSVs do SEEG por cidade (anos em colunas).
    """
    logger.info(f"Processando SEEG CSV de: {path_file}")

    try:
        df = pd.read_csv(path_file, sep=None, engine="python")
        df.columns = [c.strip() for c in df.columns]

        cidade_col = None
        for col in df.columns:
            if col.lower() in {"cidade", "municipio", "município"}:
                cidade_col = col
                break

        if not cidade_col:
            logger.error("Coluna de cidade não encontrada no SEEG CSV.")
            return pd.DataFrame()

        df = df[df[cidade_col].astype(str).str.contains(MUNICIPIO, case=False, na=False)]
        if df.empty:
            logger.warning("SEEG CSV não possui registros para o município.")
            return pd.DataFrame()

        year_cols = [c for c in df.columns if c.isdigit() and len(c) == 4]
        if not year_cols:
            logger.error("Colunas de anos não encontradas no SEEG CSV.")
            return pd.DataFrame()

        melted = df[year_cols].apply(pd.to_numeric, errors="coerce").sum().reset_index()
        melted.columns = ["ano", "valor"]
        melted["ano"] = melted["ano"].astype(int)
        melted["mes"] = 0

        return padronizar(
            melted,
            indicador="Emissões de GEE (tCO2e)",
            categoria="Sustentabilidade",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="SEEG (Observatório do Clima)",
            manual=False,
        )
    except Exception as e:
        logger.error(f"Erro ao processar SEEG CSV: {e}")
        return pd.DataFrame()

def run():
    logger.info("Iniciando ETL SEEG")
    raw_dir = DATA_DIR / "raw"
    files = [f for f in os.listdir(raw_dir) if "seeg" in f.lower()]
    
    if not files:
        logger.warning("Nenhum arquivo Excel do SEEG encontrado em data/raw")
        return pd.DataFrame()

    priority = ["ar6", "ar5", "ar4", "ar2", "gases"]
    files_sorted = sorted(
        files,
        key=lambda f: next((i for i, p in enumerate(priority) if p in f.lower()), len(priority)),
    )
    path_file = str(raw_dir / files_sorted[0])

    if path_file.lower().endswith(".csv"):
        df = process_seeg_csv(path_file)
    else:
        df = process_seeg_xls(path_file)
    
    if not df.empty:
        upsert_indicators(df, indicator_key="EMISSOES_GEE", source="SEEG", category="Sustentabilidade")
        logger.info("ETL SEEG concluído.")
    return df

if __name__ == "__main__":
    run()
