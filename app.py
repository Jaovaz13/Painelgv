"""
Ponto de entrada do painel Streamlit.
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao sys.path para garantir que os pacotes sejam encontrados
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Importar o main do painel
from panel.painel import main

if __name__ == "__main__":
    main()
