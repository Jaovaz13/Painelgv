import pandas as pd
import logging
from pathlib import Path
from config import DATA_DIR, COD_IBGE
from database import upsert_indicators

logger = logging.getLogger(__name__)

RAW_DIR = DATA_DIR / "raw"

def load_caged_regional():
    """
    Processa o arquivo 'caged MG.xls' para extrair dados de Governador Valadares.
    """
    path = RAW_DIR / "caged MG.xls"
    if not path.exists():
        logger.warning(f"Arquivo {path} não encontrado.")
        return
    
    try:
        # Lendo a aba 'municipios'
        df = pd.read_excel(path, sheet_name='municipios')
        
        # O cabeçalho real está na linha 9 (0-indexed)
        # Vamos buscar 'GOVERNADOR VALADARES' na coluna 0 ou 1
        gv_row = df[df.iloc[:, 0].astype(str).str.contains('GOVERNADOR VALADARES', case=False, na=False)]
        
        if not gv_row.empty:
            # Conforme análise: 
            # Col 3 = Saldo Mensal (Set 2019?)
            # Col 7 = Saldo no Ano (2019)
            # Col 11 = Saldo 12 Meses
            
            saldo_mes = float(gv_row.iloc[0, 3])
            saldo_ano = float(gv_row.iloc[0, 7])
            
            # Como o arquivo é de 2019, vamos salvar como dados de 2019
            # Criando DataFrames para upsert
            df_mes = pd.DataFrame([{"year": 2019, "value": saldo_mes, "unit": "Vagas (Saldo Mensal)"}])
            df_ano = pd.DataFrame([{"year": 2019, "value": saldo_ano, "unit": "Vagas (Saldo Anual)"}])
            
            upsert_indicators(df_mes, indicator_key="SALDO_CAGED_MENSAL", source="CAGED_MANUAL_MG")
            upsert_indicators(df_ano, indicator_key="SALDO_CAGED_ANUAL", source="CAGED_MANUAL_MG")
            logger.info("Dados de CAGED Regional (2019) carregados.")
    except Exception as e:
        logger.error(f"Erro ao processar caged MG.xls: {e}")

def load_demograficos_csv():
    """
    Processa arquivos idhm.csv e gini.csv.
    """
    for file, key in [("idhm.csv", "IDHM"), ("gini.csv", "GINI")]:
        path = RAW_DIR / file
        if not path.exists(): continue
        
        try:
            df = pd.read_csv(path, sep=';')
            df.columns = [c.lower() for c in df.columns]
            df = df.rename(columns={"ano": "year", "valor": "value"})
            df["unit"] = "Índice"
            upsert_indicators(df, indicator_key=key, source="MANUAL_CSV")
            logger.info(f"Dados de {key} carregados via CSV.")
        except Exception as e:
            logger.error(f"Erro ao processar {file}: {e}")

def run():
    logger.info("Iniciando carga de dados manuais extras.")
    load_caged_regional()
    load_demograficos_csv()
    logger.info("Carga de dados manuais concluída.")

if __name__ == "__main__":
    run()
