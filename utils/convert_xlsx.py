import logging
from pathlib import Path
import pandas as pd

from config import DATA_DIR

logger = logging.getLogger(__name__)

CONVERTED_DIR = DATA_DIR / "raw" / "converted"
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

def convert_csv_to_xlsx(csv_path: Path) -> Path:
    """Converte um arquivo CSV para XLSX em data/raw/converted/ e retorna o caminho."""
    try:
        df = pd.read_csv(csv_path, sep=None, engine="python")
        xlsx_path = CONVERTED_DIR / f"{csv_path.stem}.xlsx"
        df.to_excel(xlsx_path, index=False)
        logger.info(f"Convertido: {csv_path} -> {xlsx_path}")
        return xlsx_path
    except Exception as e:
        logger.error(f"Erro ao converter {csv_path}: {e}")
        return csv_path  # fallback

def prioritize_xlsx_if_exists(file_pattern: str) -> Path:
    """Retorna o caminho XLSX se existir; senão, converte o CSV correspondente."""
    raw_dir = DATA_DIR / "raw"
    candidates = list(raw_dir.glob(file_pattern))
    if not candidates:
        return None

    # Priorizar XLSX
    for f in candidates:
        if f.suffix.lower() == ".xlsx":
            return f

    # Se só houver CSV, converter
    for f in candidates:
        if f.suffix.lower() == ".csv":
            return convert_csv_to_xlsx(f)

    return None
