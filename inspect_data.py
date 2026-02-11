import pandas as pd
import os

files = [
    r'c:\painel_gv\data\raw\Base_de_Dados_IDSC-BR_2024.xlsx',
    r'c:\painel_gv\data\raw\Base_de_Dados_IDSC-BR_2025.xlsx'
]

for file_path in files:
    print(f"\n--- Inspecionando: {file_path} ---")
    if not os.path.exists(file_path):
        print("Arquivo não encontrado.")
        continue
    try:
        # Tenta ler apenas as primeiras colunas/linhas para ser rápido
        df = pd.read_excel(file_path, nrows=5)
        print("Colunas encontradas:")
        print(df.columns.tolist())
        print("Primeira linha:")
        print(df.iloc[0].to_dict())
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")

try:
    import odf
    print("\nODF instalado com sucesso.")
except ImportError:
    print("\nODF NÃO instalado.")
