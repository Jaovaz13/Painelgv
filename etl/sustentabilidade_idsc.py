import pandas as pd
import logging
import os
from etl.utils import padronizar
from config import MUNICIPIO, UF, DATA_DIR
from database import upsert_indicators

logger = logging.getLogger(__name__)

def idsc(path_file):
    """
    Processa dados do IDSC-BR. Suporta CSV e XLSX.
    """
    logger.info(f"Processando IDSC: {path_file}")
    
    try:
        # Inferir ano pelo nome do arquivo
        import re
        year_match = re.search(r"20\d{2}", path_file)
        file_year = int(year_match.group()) if year_match else None

        if path_file.endswith(".xlsx") or path_file.endswith(".xls"):
            xl = pd.ExcelFile(path_file)
            sheet_name = xl.sheet_names[0]
            # Tenta encontrar a aba de dados (geralmente a segunda ou com nome IDSC-BR)
            for s in xl.sheet_names:
                if "IDSC-BR" in s:
                    sheet_name = s
                    break
            df = pd.read_excel(path_file, sheet_name=sheet_name)
        else:
            df = pd.read_csv(path_file, sep=None, engine='python')
            
        cols_map = {
            "Município": "municipio",
            "Municipio": "municipio",
            "Cidade": "municipio",
            "Ano": "ano",
            "Year": "ano",
            "Score Geral": "valor",
            "Pontuação Geral": "valor",
            "IDSC-BR": "valor"
        }
        df = df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns})
        
        # Se não tem coluna de ano, usa o do arquivo
        if "ano" not in df.columns and file_year:
            df["ano"] = file_year
            
        if "municipio" in df.columns:
            df = df[df["municipio"].astype(str).str.contains(MUNICIPIO, case=False, na=False)]
            
        if "ano" not in df.columns or "valor" not in df.columns:
            logger.error(f"Colunas obrigatórias não encontradas no IDSC ({path_file}). Colunas: {df.columns}")
            return pd.DataFrame()
            
        df = df[["ano", "valor"]].drop_duplicates()
        df["mes"] = 0
        
        return padronizar(
            df,
            indicador="IDSC-BR",
            categoria="Sustentabilidade",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="IDSC-BR",
            manual=True
        )
    except Exception as e:
        logger.error(f"Erro ao processar IDSC ({path_file}): {e}")
        return pd.DataFrame()

def run():
    logger.info("Iniciando ETL Sustentabilidade IDSC")
    raw_dir = DATA_DIR / "raw"
    files = [f for f in os.listdir(raw_dir) if "idsc" in f.lower()]
    
    if not files:
        logger.warning("Nenhum arquivo IDSC encontrado em data/raw")
        return pd.DataFrame()

    all_dfs = []
    for f in files:
        path_file = str(raw_dir / f)
        df = idsc(path_file)
        if not df.empty:
            all_dfs.append(df)
            upsert_indicators(df, indicator_key="IDSC_GERAL", source="IDSC", category="Sustentabilidade")
    
    if all_dfs:
        logger.info(f"ETL IDSC concluído com {len(all_dfs)} arquivos.")
        return pd.concat(all_dfs)
    return pd.DataFrame()

if __name__ == "__main__":
    run()
