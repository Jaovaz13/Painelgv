from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "db"
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "raw").mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

MUNICIPIO = os.getenv("MUNICIPIO", "Governador Valadares")
COD_IBGE = os.getenv("COD_IBGE", "3127701")
UF = os.getenv("UF", "MG")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'indicadores.db'}",
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

SCHEDULER_INTERVAL_HOURS = int(os.getenv("SCHEDULER_INTERVAL_HOURS", "24"))
