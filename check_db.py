import sqlite3
import os

# Baseado no config.py
db_path = r'c:\painel_gv\data\indicadores.db'
if not os.path.exists(db_path):
    print(f"Erro: Banco não encontrado em {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT indicator_key, COUNT(*) FROM indicators GROUP BY indicator_key")
        rows = cursor.fetchall()
        if not rows:
            print("Banco vazio ou sem registros na tabela indicators.")
        else:
            for row in rows:
                print(f"{row[0]}: {row[1]} registros")
    except Exception as e:
        print(f"Erro ao acessar tabela: {e}")
    conn.close()

print("\nArquivos em data/raw:")
for f in os.listdir(r'c:\painel_gv\data\raw'):
    size = os.path.getsize(os.path.join(r'c:\painel_gv\data\raw', f))
    print(f"- {f} ({size / 1024 / 1024:.2f} MB)")
