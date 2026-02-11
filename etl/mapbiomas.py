import logging
from pathlib import Path
import glob

import pandas as pd

from config import DATA_DIR
from database import upsert_indicators


logger = logging.getLogger(__name__)


def find_mapbiomas_files() -> list[Path]:
    """Encontra todos os arquivos MapBiomas na pasta data/raw"""
    raw_dir = DATA_DIR / "raw"
    mapbiomas_files = []
    
    # Procura por arquivos que contenham "mapbiomas" no nome (case insensitive)
    for pattern in ["*mapbiomas*", "*MapBiomas*", "*MAPBIOMAS*"]:
        mapbiomas_files.extend(glob.glob(str(raw_dir / pattern)))
    
    # Converte para objetos Path e remove duplicatas
    unique_files = list({Path(f) for f in mapbiomas_files})
    logger.info(f"Encontrados {len(unique_files)} arquivos MapBiomas: {[f.name for f in unique_files]}")
    return unique_files


def load_mapbiomas_file(path: Path) -> pd.DataFrame:
    """Carrega arquivo MapBiomas (CSV ou Excel)"""
    logger.info("Carregando dados MapBiomas de %s", path)
    
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path, encoding='utf-8')
    elif path.suffix.lower() in ['.xlsx', '.xls']:
        # Tenta diferentes headers para arquivos Excel
        try:
            df = pd.read_excel(path, header=0)
            if df.iloc[:, 0].isna().all():
                df = pd.read_excel(path, header=5)
            if df.iloc[:, 0].isna().all():
                df = pd.read_excel(path, header=10)
            return df
        except Exception:
            # Última tentativa sem header
            return pd.read_excel(path, header=None)
    else:
        logger.warning(f"Formato não suportado: {path.suffix}")
        return pd.DataFrame()


def transform_mapbiomas(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """
    Transforma dados MapBiomas conforme o tipo de arquivo
    """
    if df.empty:
        return pd.DataFrame(columns=["year", "value", "unit"])

    # Normaliza colunas para minúsculas
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Verifica se é o formato com colunas de anos numéricas
    year_columns = [col for col in df.columns if col.isdigit() and len(col) == 4]
    if year_columns:
        return transform_year_format_mapbiomas(df, source_file)
    # Determina o tipo de indicador baseado no nome do arquivo
    elif "fogo" in source_file.lower():
        return transform_fogo(df)
    elif "agricultura" in source_file.lower():
        return transform_agricultura(df)
    elif "urban" in source_file.lower():
        return transform_urban(df)
    else:
        # Tenta transformação genérica
        return transform_generic_mapbiomas(df)


def transform_year_format_mapbiomas(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """Transforma formato com colunas de anos para MapBiomas"""
    result_data = []
    
    # Identifica colunas de anos
    year_columns = [col for col in df.columns if col.isdigit() and len(col) == 4]
    year_columns.sort()  # Ordena cronologicamente
    
    # Filtra para Governador Valadares se houver coluna de município
    if 'municipio' in df.columns or 'municipality' in df.columns:
        municipio_col = 'municipio' if 'municipio' in df.columns else 'municipality'
        gv_df = df[df[municipio_col].str.contains('Governador Valadares', case=False, na=False)]
        if not gv_df.empty:
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
                    "unit": "Hectares"
                })
    
    return pd.DataFrame(result_data)


def transform_fogo(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados de focos de fogo MapBiomas"""
    result_data = []
    
    # Procura colunas de ano e valores
    year_cols = [col for col in df.columns if 'ano' in col]
    value_cols = [col for col in df.columns if any(x in col for x in ['fogo', 'focos', 'queimada', 'incendio'])]
    
    if not year_cols or not value_cols:
        logger.warning("Colunas de ano ou focos de fogo não encontradas")
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
                            "unit": "Focos de fogo"
                        })
    
    return pd.DataFrame(result_data)


def transform_agricultura(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados de agricultura MapBiomas"""
    result_data = []
    
    year_cols = [col for col in df.columns if 'ano' in col]
    value_cols = [col for col in df.columns if any(x in col for x in ['agricultura', 'area', 'hectare'])]
    
    if not year_cols or not value_cols:
        logger.warning("Colunas de ano ou agricultura não encontradas")
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
                            "unit": "Hectares"
                        })
    
    return pd.DataFrame(result_data)


def transform_urban(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados de área urbana MapBiomas"""
    result_data = []
    
    year_cols = [col for col in df.columns if 'ano' in col]
    value_cols = [col for col in df.columns if any(x in col for x in ['urban', 'area', 'hectare'])]
    
    if not year_cols or not value_cols:
        logger.warning("Colunas de ano ou área urbana não encontradas")
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
                            "unit": "Hectares"
                        })
    
    return pd.DataFrame(result_data)


def transform_generic_mapbiomas(df: pd.DataFrame) -> pd.DataFrame:
    """Transformação genérica para outros arquivos MapBiomas"""
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
                                "unit": "Hectares"
                            })
                        except (ValueError, TypeError):
                            continue
    
    return pd.DataFrame(result_data)


def run() -> None:
    """
    Executa ETL MapBiomas processando todos os arquivos encontrados
    """
    logger.info("Iniciando ETL MapBiomas.")
    
    mapbiomas_files = find_mapbiomas_files()
    
    if not mapbiomas_files:
        logger.warning(
            "Nenhum arquivo MapBiomas encontrado em data/raw. "
            "Indicadores de sustentabilidade (AREA_URBANA, VEGETACAO_NATIVA, USO_AGROPECUARIO) não serão carregados. "
            "Baixe os arquivos necessários em https://mapbiomas.org/ e coloque em data/raw/"
        )
        return
    
    total_inserted = 0
    
    for file_path in mapbiomas_files:
        try:
            df_raw = load_mapbiomas_file(file_path)
            if df_raw.empty:
                logger.warning(f"Arquivo {file_path.name} está vazio ou não pôde ser lido")
                continue
                
            df = transform_mapbiomas(df_raw, file_path.name)
            if df.empty:
                logger.warning(f"Nenhum dado transformado do arquivo {file_path.name}")
                continue
            
            # Define indicator_key baseado no tipo de arquivo
            if "fogo" in file_path.name.lower():
                indicator_key = "MAPBIOMAS_FOGO"
            elif "agricultura" in file_path.name.lower():
                indicator_key = "MAPBIOMAS_AGRICULTURA"
            elif "urban" in file_path.name.lower():
                indicator_key = "MAPBIOMAS_URBAN"
            else:
                indicator_key = "MAPBIOMAS_GERAL"
            
            inserted = upsert_indicators(df, indicator_key=indicator_key, source="MAPBIOMAS")
            total_inserted += inserted
            logger.info(f"Arquivo {file_path.name}: {inserted} registros novos")
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_path.name}: {e}")
            continue
    
    logger.info(f"ETL MapBiomas concluído. Total de registros novos: {total_inserted}")

