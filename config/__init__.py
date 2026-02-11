from pathlib import Path
import os

# Pasta raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configurações do Município
MUNICIPIO = os.getenv("MUNICIPIO", "Governador Valadares")
COD_IBGE = os.getenv("COD_IBGE", "3127701")
UF = os.getenv("UF", "MG")

# Diretórios de Dados
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
LOGS_DIR = BASE_DIR / "logs"
DB_DIR = BASE_DIR / "db"

# Garantir que pastas existam
for d in [DATA_DIR, RAW_DIR, LOGS_DIR, DB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# URL do Banco de Dados
# Prioriza variável de ambiente (Deploy/Cloud)
# Se não houver, usa SQLite local em data/indicadores.db
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite:///{DATA_DIR}/indicadores.db"
)

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

# Categorias de Indicadores
CATEGORIAS = [
    "Economia", 
    "Trabalho e Renda", 
    "Saúde", 
    "Educação", 
    "Sustentabilidade", 
    "Demografia"
]

SCHEDULER_INTERVAL_HOURS = int(os.getenv("SCHEDULER_INTERVAL_HOURS", "24"))
