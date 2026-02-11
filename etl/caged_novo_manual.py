import pandas as pd
import logging
from pathlib import Path
from config import DATA_DIR, COD_IBGE
from database import upsert_indicators

logger = logging.getLogger(__name__)

def run():
    path = DATA_DIR / "raw" / "caged tabelas_Dezembro de 2025.xlsx"
    if not path.exists():
        logger.warning(f"Arquivo {path} não encontrado.")
        return

    logger.info("Processando Novo CAGED complexo (Dez/2025)...")
    
    try:
        # Tabela 8 tem dados por município
        # Lendo apenas colunas essenciais para encontrar a linha e os dados recentes
        # Geralmente: Col 1 = UF, Col 2 = Municipio, Col 3 = Cod, ...
        xl = pd.ExcelFile(path)
        
        # Vamos tentar ler Tabela 8
        df = pd.read_excel(path, sheet_name='Tabela 8')
        
        # Procurar pela linha de Valadares usando o código ou nome
        # O código IBGE completo tem 7 dígitos (3127701)
        mask = df.astype(str).apply(lambda row: row.str.contains('3127701').any(), axis=1)
        gv_row = df[mask]
        
        if not gv_row.empty:
            # Pegar o último valor da linha e tentar converter para número
            # Usamos pd.to_numeric para ignorar erros e lidar com strings de rodapé ou vazias
            row_data = gv_row.iloc[0]
            for val in reversed(row_data.values):
                val_num = pd.to_numeric(val, errors='coerce')
                if not pd.isna(val_num):
                    df_save = pd.DataFrame([{"year": 2024, "value": float(val_num), "unit": "Vagas (Saldo)"}])
                    upsert_indicators(df_save, indicator_key="EMPREGOS_CAGED", source="CAGED_MANUAL_XLSX")
                    logger.info("Saldo do CAGED atualizado via arquivo manual XLSX.")
                    break
            
        # Tabela 9: Salário Médio
        df_sal = pd.read_excel(path, sheet_name='Tabela 9')
        mg_row = df_sal[df_sal.astype(str).apply(lambda row: row.str.contains('Minas Gerais', case=False).any(), axis=1)]
        if not mg_row.empty:
            row_data_sal = mg_row.iloc[0]
            for val in reversed(row_data_sal.values):
                val_sal = pd.to_numeric(val, errors='coerce')
                if not pd.isna(val_sal) and val_sal > 100: # Filtro simples para ignorar códigos
                    df_sal_save = pd.DataFrame([{"year": 2024, "value": float(val_sal), "unit": "R$"}])
                    upsert_indicators(df_sal_save, indicator_key="SALARIO_MEDIO_MG", source="CAGED_MANUAL_MG")
                    break
            
    except Exception as e:
        logger.error(f"Erro ao processar as tabelas do CAGED: {e}")

if __name__ == "__main__":
    run()
