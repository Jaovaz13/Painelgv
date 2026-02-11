import pandas as pd
import os

idsc_file = r'c:\painel_gv\data\raw\Base_de_Dados_IDSC-BR_2024.xlsx'
print(f"--- Sheets em {idsc_file} ---")
try:
    xl = pd.ExcelFile(idsc_file)
    print(xl.sheet_names)
except Exception as e:
    print(f"Erro: {e}")

seeg_file = r'c:\painel_gv\data\raw\seeg.xlsx'
print(f"\n--- Primeiros 100 bytes de {seeg_file} ---")
try:
    with open(seeg_file, 'rb') as f:
        print(f.read(100))
except Exception as e:
    print(f"Erro: {e}")
