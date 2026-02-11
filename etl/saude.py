import pandas as pd
import logging
import os
from etl.utils import padronizar
from config import MUNICIPIO, UF, DATA_DIR
from database import upsert_indicators

logger = logging.getLogger(__name__)

def mortalidade_infantil(path_csv):
    """
    Processa dados de mortalidade infantil (DataSUS).
    Expectativa: Colunas "Ano", "Óbitos", "Municipio".
    """
    logger.info(f"Processando mortalidade infantil do arquivo: {path_csv}")
    
    try:
        df = pd.read_csv(path_csv)
        
        cols_map = {
            "Município": "municipio",
            "Municipio": "municipio",
            "Ano": "ano",
            "Óbitos": "valor",
            "Obitos": "valor"
        }
        df = df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns})
        
        if "municipio" in df.columns:
            df = df[df["municipio"] == MUNICIPIO]
            
        if "ano" not in df.columns or "valor" not in df.columns:
            logger.error(f"Colunas obrigatórias não encontradas no DataSUS. Colunas: {df.columns}")
            return pd.DataFrame()
            
        df = df.groupby("ano")["valor"].sum().reset_index()
        df["mes"] = 0
        
        return padronizar(
            df,
            indicador="Mortalidade infantil",
            categoria="Saúde",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="DataSUS",
            manual=True
        )
    except Exception as e:
        logger.error(f"Erro ao processar mortalidade infantil DataSUS: {e}")
        return pd.DataFrame()

def run():
    logger.info("Iniciando ETL Saúde DataSUS")
    raw_dir = DATA_DIR / "raw"
    files = [f for f in os.listdir(raw_dir) if "datasus" in f.lower() or "obitos" in f.lower() or "mortalidade" in f.lower()]
    
    if not files:
        logger.warning("Nenhum arquivo DataSUS encontrado em data/raw")
        return

    path_file = str(raw_dir / files[0])
    df = mortalidade_infantil(path_file)
    
    if not df.empty:
        upsert_indicators(df, indicator_key="MORTALIDADE_INFANTIL", source="DATASUS", category="Saúde")
        logger.info("ETL Saúde DataSUS concluído.")
    else:
        logger.warning("Nenhum dado de saúde processado.")
    return df

if __name__ == "__main__":
    run()
