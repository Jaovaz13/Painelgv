import pandas as pd
import logging
import os
from etl.utils import padronizar
from config import MUNICIPIO, UF, DATA_DIR
from database import upsert_indicators

logger = logging.getLogger(__name__)

def vaf_sefaz(path_xls):
    """
    Processa dados do VAF (Valor Adicionado Fiscal) da SEFAZ-MG.
    Expectativa: Colunas "Ano", "Valor Adicionado", "Município".
    """
    logger.info(f"Processando VAF do arquivo: {path_xls}")
    
    try:
        df = pd.read_excel(path_xls)
        
        # Normalização mínima de colunas
        cols_map = {
            "Município": "municipio",
            "Municipio": "municipio",
            "Ano": "ano",
            "Valor Adicionado": "valor"
        }
        df = df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns})
        
        if "municipio" in df.columns:
            df = df[df["municipio"] == MUNICIPIO]
            
        if "ano" not in df.columns or "valor" not in df.columns:
            logger.error(f"Colunas obrigatórias não encontradas no VAF. Colunas: {df.columns}")
            return pd.DataFrame()
            
        df = df[["ano", "valor"]]
        df["mes"] = 0
        
        return padronizar(
            df,
            indicador="Valor Adicionado Fiscal",
            categoria="Economia",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="SEFAZ-MG",
            manual=True
        )
    except Exception as e:
        logger.error(f"Erro ao processar VAF: {e}")
        return pd.DataFrame()

def run():
    logger.info("Iniciando ETL SEFAZ (VAF e ICMS)")
    raw_dir = DATA_DIR / "raw"
    
    # Processar VAF
    vaf_files = [f for f in os.listdir(raw_dir) if "vaf" in f.lower()]
    if vaf_files:
        path_vaf = str(raw_dir / vaf_files[0])
        df_vaf = vaf_sefaz(path_vaf)
        if not df_vaf.empty:
            upsert_indicators(df_vaf, indicator_key="RECEITA_VAF", source="SEFAZ_MG", category="Economia")
            logger.info("VAF processado com sucesso.")
    else:
        logger.warning("Nenhum arquivo de VAF encontrado.")

    # Processar ICMS
    icms_files = [f for f in os.listdir(raw_dir) if "icms" in f.lower()]
    if icms_files:
        path_icms = str(raw_dir / icms_files[0])
        df_icms = vaf_sefaz(path_icms) # Reutiliza a lógica de transformação
        if not df_icms.empty:
            upsert_indicators(df_icms, indicator_key="RECEITA_ICMS", source="SEFAZ_MG", category="Economia")
            logger.info("ICMS processado com sucesso.")
    else:
        logger.warning("Nenhum arquivo de ICMS encontrado.")
        
    return pd.DataFrame() # Retorno dummy para run_all

if __name__ == "__main__":
    run()
