import logging
import glob
from pathlib import Path
import pandas as pd
from typing import List

from config import DATA_DIR, COD_IBGE, MUNICIPIO
from database import upsert_indicators
from utils.convert_xlsx import convert_csv_to_xlsx

logger = logging.getLogger(__name__)


def find_sebrae_files() -> list[Path]:
    """Encontra todos os arquivos SEBRAE na pasta data/raw"""
    raw_dir = DATA_DIR / "raw"
    sebrae_files = []
    
    # Procura por arquivos que contenham "sebrae" no nome (case insensitive)
    for pattern in ["*sebrae*", "*Sebrae*", "*SEBRAE*"]:
        sebrae_files.extend(glob.glob(str(raw_dir / pattern)))
    
    # Converte para objetos Path e remove duplicatas
    unique_files = list({Path(f) for f in sebrae_files})
    logger.info(f"Encontrados {len(unique_files)} arquivos SEBRAE: {[f.name for f in unique_files]}")
    return unique_files


def load_sebrae_file(path: Path) -> pd.DataFrame:
    """Carrega arquivo SEBRAE (CSV ou Excel)"""
    logger.info("Carregando dados Sebrae de %s", path)
    
    if path.suffix.lower() == '.csv':
        # Tenta diferentes delimitadores e encodings
        try:
            # Primeiro tenta com ponto e vírgula (mais comum no Brasil)
            df = pd.read_csv(path, encoding='utf-8', delimiter=';')
        except:
            try:
                # Depois com vírgula
                df = pd.read_csv(path, encoding='utf-8')
            except:
                # Por último com latin-1
                df = pd.read_csv(path, encoding='latin-1', delimiter=';')
        return df
    elif path.suffix.lower() in ['.xlsx', '.xls']:
        return pd.read_excel(path)
    else:
        logger.warning(f"Formato não suportado: {path.suffix}")
        return pd.DataFrame()


def transform_sebrae(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """
    Transforma dados SEBRAE conforme o tipo de arquivo
    """
    if df.empty:
        return pd.DataFrame(columns=["year", "value", "unit"])

    # Normaliza colunas para minúsculas e remove espaços
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Verifica se é o formato do test_sebrae.csv
    if 'municipio' in df.columns and 'ano' in df.columns and ('empregos' in df.columns or 'estabelecimentos' in df.columns):
        return transform_test_format(df)
    # Verifica se é o formato principal (Year, Number workers)
    elif 'year' in df.columns and 'number workers' in df.columns:
        return transform_workers_format(df)
    # Verifica outros formatos específicos
    elif "empregados" in source_file.lower():
        return transform_empregados(df)
    elif "estabelecimentos" in source_file.lower():
        return transform_estabelecimentos(df)
    elif "evolucao" in source_file.lower():
        return transform_evolucao(df)
    else:
        # Tenta transformação genérica
        return transform_generic(df)


def transform_test_format(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma formato do test_sebrae.csv"""
    result_data = []
    
    # Para cada linha, cria registros para empregos e estabelecimentos
    for _, row in df.iterrows():
        year = int(row['ano'])
        
        # Adiciona empregos se existir
        if 'empregos' in df.columns and pd.notna(row['empregos']):
            result_data.append({
                "year": year,
                "value": float(row['empregos']),
                "unit": "Empregos"
            })
        
        # Adiciona estabelecimentos se existir
        if 'estabelecimentos' in df.columns and pd.notna(row['estabelecimentos']):
            result_data.append({
                "year": year,
                "value": float(row['estabelecimentos']),
                "unit": "Estabelecimentos"
            })
    
    return pd.DataFrame(result_data)


def transform_workers_format(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma formato principal: Year, Number workers"""
    result_data = []
    
    # Agrupa por ano e soma todos os trabalhadores
    grouped = df.groupby('year')['number workers'].sum().reset_index()
    
    for _, row in grouped.iterrows():
        result_data.append({
            "year": int(row['year']),
            "value": float(row['number workers']),
            "unit": "Trabalhadores"
        })
    
    return pd.DataFrame(result_data)


def transform_empregados(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados de empregados SEBRAE"""
    result_data = []
    
    # Procura colunas de ano e valores
    year_cols = [col for col in df.columns if 'ano' in col]
    value_cols = [col for col in df.columns if 'empreg' in col or 'valor' in col]
    
    if not year_cols or not value_cols:
        logger.warning("Colunas de ano ou valor não encontradas")
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
                            "unit": "Empregados"
                        })
    
    return pd.DataFrame(result_data)


def transform_estabelecimentos(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados de estabelecimentos SEBRAE"""
    result_data = []
    
    year_cols = [col for col in df.columns if 'ano' in col]
    value_cols = [col for col in df.columns if 'estabelec' in col or 'empresa' in col]
    
    if not year_cols or not value_cols:
        logger.warning("Colunas de ano ou estabelecimentos não encontradas")
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
                            "unit": "Estabelecimentos"
                        })
    
    return pd.DataFrame(result_data)


def transform_evolucao(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma dados de evolução SEBRAE"""
    return transform_generic(df)


def transform_generic(df: pd.DataFrame) -> pd.DataFrame:
    """Transformação genérica para outros arquivos SEBRAE"""
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
                                "unit": "Unidades"
                            })
                        except (ValueError, TypeError):
                            continue
    
    return pd.DataFrame(result_data)


def run() -> None:
    """
    Executa ETL SEBRAE processando todos os arquivos encontrados
    """
    logger.info("Iniciando ETL SEBRAE.")
    
    sebrae_files = find_sebrae_files()
    
    if not sebrae_files:
        logger.warning("Nenhum arquivo SEBRAE encontrado em data/raw")
        return
    
    total_inserted = 0
    
    for file_path in sebrae_files:
        try:
            df_raw = load_sebrae_file(file_path)
            if df_raw.empty:
                logger.warning(f"Arquivo {file_path.name} está vazio ou não pôde ser lido")
                continue
                
            df = transform_sebrae(df_raw, file_path.name)
            if df.empty:
                logger.warning(f"Nenhum dado transformado do arquivo {file_path.name}")
                continue
            
            # Define indicator_key baseado no tipo de arquivo
            if "empregados" in file_path.name.lower():
                indicator_key = "SEBRAE_EMPREGADOS"
            elif "estabelecimentos" in file_path.name.lower():
                indicator_key = "SEBRAE_ESTABELECIMENTOS"
            elif "evolucao" in file_path.name.lower():
                indicator_key = "SEBRAE_EVOLUCAO"
            else:
                indicator_key = "SEBRAE_GERAL"
            
            inserted = upsert_indicators(df, indicator_key=indicator_key, source="SEBRAE", 
                                         category="Negócios", manual=True)
            total_inserted += inserted
            logger.info(f"Arquivo {file_path.name}: {inserted} registros novos")
            
            # Converte CSV para XLSX após processamento bem-sucedido
            if file_path.suffix.lower() == '.csv' and inserted > 0:
                convert_csv_to_xlsx(file_path)
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_path.name}: {e}")
            continue
    
    logger.info(f"ETL SEBRAE concluído. Total de registros novos: {total_inserted}")
