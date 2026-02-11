import pandas as pd
import logging
from etl.utils import padronizar
from config import MUNICIPIO, UF, DATA_DIR
from database import upsert_indicators
import os

logger = logging.getLogger(__name__)

def rais_empregos(path_file):
    """
    Processa dados da RAIS a partir de um arquivo local (CSV ou Excel).
    """
    logger.info(f"Processando RAIS do arquivo: {path_file}")
    
    try:
        if path_file.endswith('.csv'):
            df = pd.read_csv(path_file, sep=";")
        else:
            df = pd.read_excel(path_file)
            
        # Filtro para o município (usando o nome conforme sugestão do usuário)
        # Nota: Pode ser necessário ajustar o nome da coluna dependendo do arquivo real
        municipio_col = "Município" if "Município" in df.columns else "municipio"
        df = df[df[municipio_col] == MUNICIPIO]
        
        ano_col = "Ano" if "Ano" in df.columns else "ano"
        vinculos_col = "Vínculos Ativos" if "Vínculos Ativos" in df.columns else "vinculos"
        
        df = df.groupby(ano_col).agg({vinculos_col: "sum"}).reset_index()
        df.columns = ["ano", "valor"]
        df["mes"] = 0
        
        return padronizar(
            df,
            indicador="Empregos formais (estoque)",
            categoria="Trabalho e Renda",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="RAIS",
            manual=True
        )
    except Exception as e:
        logger.error(f"Erro ao processar RAIS: {e}")
        return pd.DataFrame()

def run():
    logger.info("Iniciando ETL RAIS")
    
    # Busca arquivo na pasta raw
    raw_dir = DATA_DIR / "raw"
    files = [f for f in os.listdir(raw_dir) if "rais" in f.lower()]
    
    if not files:
        logger.warning("Nenhum arquivo RAIS encontrado em data/raw")
        return

    # Processa o arquivo mais recente ou o primeiro encontrado
    path_file = str(raw_dir / files[0])
    df = rais_empregos(path_file)
    
    if not df.empty:
        upsert_indicators(df, indicator_key="EMPREGOS_RAIS", source="RAIS", category="Trabalho e Renda")
        logger.info("ETL RAIS concluído.")
    else:
        logger.warning("Nenhum dado de RAIS processado.")
    return df

if __name__ == "__main__":
    run()
