import pandas as pd
import os

idsc_files = [
    r'c:\painel_gv\data\raw\Base_de_Dados_IDSC-BR_2023.xlsx',
    r'c:\painel_gv\data\raw\Base_de_Dados_IDSC-BR_2024.xlsx',
    r'c:\painel_gv\data\raw\Base_de_Dados_IDSC-BR_2025.xlsx'
]

for f in idsc_files:
    if not os.path.exists(f): continue
    print(f"\n--- {f} ---")
    try:
        xl = pd.ExcelFile(f)
        for sheet in xl.sheet_names:
            df = pd.read_excel(f, sheet_name=sheet, nrows=5)
            print(f"Sheet: {sheet} | Cols: {df.columns.tolist()[:5]}...")
            if any(c in [col.lower() for col in df.columns] for p in ['municipio', 'município', 'city']):
                print(f"  -> POSSÍVEL SHEET DE DADOS!")
    except Exception as e:
        print(f"Erro: {e}")
