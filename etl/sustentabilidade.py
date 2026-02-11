import logging
from pathlib import Path
import glob

import pandas as pd

from config import COD_IBGE, DATA_DIR
from database import upsert_indicators

logger = logging.getLogger(__name__)


def find_idsc_files() -> list[Path]:
    """Encontra todos os arquivos IDSC na pasta data/raw"""
    raw_dir = DATA_DIR / "raw"
    idsc_files = []
    
    # Procura por arquivos que contenham "idsc" no nome (case insensitive)
    for pattern in ["*idsc*", "*IDSC*"]:
        idsc_files.extend(glob.glob(str(raw_dir / pattern)))
    
    # Converte para objetos Path e remove duplicatas
    unique_files = list({Path(f) for f in idsc_files})
    logger.info(f"Encontrados {len(unique_files)} arquivos IDSC: {[f.name for f in unique_files]}")
    return unique_files


def load_idsc_file(path: Path) -> pd.DataFrame:
    """Carrega arquivo IDSC (CSV ou Excel)"""
    logger.info("Carregando dados IDSC de %s", path)
    
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path, encoding='utf-8')
    elif path.suffix.lower() in ['.xlsx', '.xls']:
        return pd.read_excel(path)
    else:
        logger.warning(f"Formato não suportado: {path.suffix}")
        return pd.DataFrame()


def transform_idsc(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados IDSC"""
    if df.empty:
        return pd.DataFrame(columns=["year", "value", "unit"])

    # Normaliza colunas para minúsculas
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Filtrar pelo cod ibge se existir coluna
    if "codigo_ibge" in df.columns:
        df = df[df["codigo_ibge"].astype(str) == str(COD_IBGE)]
        
    # Mapear colunas
    df = df.rename(columns={"ano": "year", "idsc": "value", "indice": "value"})
    
    if "year" not in df.columns or "value" not in df.columns:
        logger.warning("Colunas year ou value não encontradas")
        return pd.DataFrame(columns=["year", "value", "unit"])
        
    df["unit"] = "Índice (0-100)"
    return df


def run_idsc() -> int:
    """Processa todos os arquivos IDSC encontrados"""
    idsc_files = find_idsc_files()
    
    if not idsc_files:
        logger.warning("Nenhum arquivo IDSC encontrado em data/raw")
        return 0
    
    total_inserted = 0
    
    for file_path in idsc_files:
        try:
            df_raw = load_idsc_file(file_path)
            if df_raw.empty:
                logger.warning(f"Arquivo {file_path.name} está vazio ou não pôde ser lido")
                continue
                
            df = transform_idsc(df_raw)
            if df.empty:
                logger.warning(f"Nenhum dado transformado do arquivo {file_path.name}")
                continue
            
            inserted = upsert_indicators(df, indicator_key="IDSC_GERAL", source="CIDADES_SUSTENTAVEIS")
            total_inserted += inserted
            logger.info(f"Arquivo {file_path.name}: {inserted} registros novos")
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_path.name}: {e}")
            continue
    
    return total_inserted


def run_saneamento(filename: str = "snis.csv") -> int:
    """Processa dados de saneamento SNIS"""
    path = DATA_DIR / "raw" / filename
    if not path.exists():
        logger.warning(f"Arquivo SNIS não encontrado: {path}")
        return 0
        
    try:
        df = pd.read_csv(path, sep=";")
        df.columns = [c.lower() for c in df.columns]
        
        # Mapear
        df = df.rename(columns={"ano": "year", "indice": "value", "saneamento": "value", "valor": "value"})
        
        if "year" not in df.columns or "value" not in df.columns:
            return 0
            
        df["unit"] = "% Cobertura"
        return upsert_indicators(df, indicator_key="SANEAMENTO_BASICO", source="SNIS")
    except Exception as e:
        logger.exception("Erro no ETL SNIS: %s", e)
        return 0


def run() -> None:
    """Executa ETL completo de Sustentabilidade"""
    logger.info("--- Iniciando ETL Sustentabilidade ---")
    run_idsc()
    run_saneamento()
    logger.info("--- Fim ETL Sustentabilidade ---")
