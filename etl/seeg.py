import logging
from pathlib import Path
import glob

import pandas as pd

from config import DATA_DIR
from database import upsert_indicators


logger = logging.getLogger(__name__)


def find_seeg_files() -> list[Path]:
    """Encontra todos os arquivos SEEG na pasta data/raw"""
    raw_dir = DATA_DIR / "raw"
    seeg_files = []
    
    # Procura por arquivos que contenham "seeg" no nome (case insensitive)
    for pattern in ["*seeg*", "*SEEG*"]:
        seeg_files.extend(glob.glob(str(raw_dir / pattern)))
    
    # Converte para objetos Path e remove duplicatas
    unique_files = list({Path(f) for f in seeg_files})
    logger.info(f"Encontrados {len(unique_files)} arquivos SEEG: {[f.name for f in unique_files]}")
    return unique_files


def load_seeg_file(path: Path) -> pd.DataFrame:
    """Carrega arquivo SEEG (CSV ou Excel)"""
    logger.info("Carregando dados SEEG de %s", path)
    
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path, encoding='utf-8')
    elif path.suffix.lower() in ['.xlsx', '.xls']:
        return pd.read_excel(path)
    else:
        logger.warning(f"Formato não suportado: {path.suffix}")
        return pd.DataFrame()


def transform_seeg(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """
    Transforma dados SEEG conforme o tipo de arquivo
    """
    if df.empty:
        return pd.DataFrame(columns=["year", "value", "unit"])

    # Normaliza colunas para minúsculas
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Verifica se é o formato principal com colunas de anos numéricas
    year_columns = [col for col in df.columns if col.isdigit() and len(col) == 4]
    if year_columns:
        return transform_year_format(df, source_file)
    # Determina o tipo de indicador baseado no nome do arquivo
    elif "gases" in source_file.lower():
        return transform_gases(df)
    elif "ar" in source_file.lower():
        return transform_ar(df)
    else:
        # Tenta transformação genérica
        return transform_generic_seeg(df)


def transform_year_format(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """Transforma formato com colunas de anos (1970, 1971, etc)"""
    result_data = []
    
    # Identifica colunas de anos
    year_columns = [col for col in df.columns if col.isdigit() and len(col) == 4]
    year_columns.sort()  # Ordena cronologicamente
    
    # Filtra para Governador Valadares se houver coluna de cidade
    if 'cidade' in df.columns:
        gv_df = df[df['cidade'].str.contains('Governador Valadares', case=False, na=False)]
        if gv_df.empty:
            logger.warning("Governador Valadares não encontrado nos dados SEEG")
            return pd.DataFrame(columns=["year", "value", "unit"])
        df = gv_df
    
    # Para cada ano, soma todos os valores
    for year in year_columns:
        if year in df.columns:
            # Converte para numérico, tratando erros
            year_values = pd.to_numeric(df[year], errors='coerce')
            total_value = year_values.sum()
            
            if pd.notna(total_value) and total_value > 0:
                result_data.append({
                    "year": int(year),
                    "value": float(total_value),
                    "unit": "toneladas CO2"
                })
    
    return pd.DataFrame(result_data)


def transform_gases(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados de emissões de gases SEEG"""
    result_data = []
    
    # Procura colunas de ano e valores
    year_cols = [col for col in df.columns if 'ano' in col]
    value_cols = [col for col in df.columns if any(x in col for x in ['emissao', 'co2', 'gases', 'valor'])]
    
    if not year_cols or not value_cols:
        logger.warning("Colunas de ano ou emissões não encontradas")
        return pd.DataFrame(columns=["year", "value", "unit"])
    
    for _, row in df.iterrows():
        for year_col in year_cols:
            year = row[year_col]
            if pd.notna(year):
                for val_col in value_cols:
                    value = row[val_col]
                    if pd.notna(value):
                        result_data.append({
                            "year": int(year),
                            "value": float(value),
                            "unit": "toneladas CO2"
                        })
    
    return pd.DataFrame(result_data)


def transform_ar(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados de emissões atmosféricas SEEG"""
    result_data = []
    
    year_cols = [col for col in df.columns if 'ano' in col]
    value_cols = [col for col in df.columns if any(x in col for x in ['emissao', 'co2', 'valor'])]
    
    if not year_cols or not value_cols:
        logger.warning("Colunas de ano ou emissões não encontradas")
        return pd.DataFrame(columns=["year", "value", "unit"])
    
    for _, row in df.iterrows():
        for year_col in year_cols:
            year = row[year_col]
            if pd.notna(year):
                for val_col in value_cols:
                    value = row[val_col]
                    if pd.notna(value):
                        result_data.append({
                            "year": int(year),
                            "value": float(value),
                            "unit": "toneladas CO2"
                        })
    
    return pd.DataFrame(result_data)


def transform_generic_seeg(df: pd.DataFrame) -> pd.DataFrame:
    """Transformação genérica para outros arquivos SEEG"""
    result_data = []
    
    # Tenta encontrar padrões genéricos
    for _, row in df.iterrows():
        for col in df.columns:
            if 'ano' in col.lower() and pd.notna(row[col]):
                year = int(row[col])
                # Procura colunas com valores numéricos
                for val_col in df.columns:
                    if val_col != col and pd.notna(row[val_col]):
                        try:
                            value = float(row[val_col])
                            result_data.append({
                                "year": year,
                                "value": value,
                                "unit": "toneladas CO2"
                            })
                        except (ValueError, TypeError):
                            continue
    
    return pd.DataFrame(result_data)


def run() -> None:
    """
    Executa ETL SEEG processando todos os arquivos encontrados
    """
    logger.info("Iniciando ETL SEEG.")
    
    seeg_files = find_seeg_files()
    
    if not seeg_files:
        logger.warning("Nenhum arquivo SEEG encontrado em data/raw")
        return
    
    total_inserted = 0
    
    for file_path in seeg_files:
        try:
            df_raw = load_seeg_file(file_path)
            if df_raw.empty:
                logger.warning(f"Arquivo {file_path.name} está vazio ou não pôde ser lido")
                continue
                
            df = transform_seeg(df_raw, file_path.name)
            if df.empty:
                logger.warning(f"Nenhum dado transformado do arquivo {file_path.name}")
                continue
            
            # Define indicator_key baseado no tipo de arquivo
            if "gases" in file_path.name.lower():
                indicator_key = "SEEG_GASES"
            elif "ar" in file_path.name.lower():
                indicator_key = "SEEG_AR"
            else:
                indicator_key = "SEEG_GERAL"
            
            inserted = upsert_indicators(df, indicator_key=indicator_key, source="SEEG")
            total_inserted += inserted
            logger.info(f"Arquivo {file_path.name}: {inserted} registros novos")
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_path.name}: {e}")
            continue
    
    logger.info(f"ETL SEEG concluído. Total de registros novos: {total_inserted}")
