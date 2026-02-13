import pandas as pd
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.utils import padronizar
from config import MUNICIPIO, UF, DATA_DIR
from database import upsert_indicators

logger = logging.getLogger(__name__)

def matriculas(path_file):
    """
    Processa dados de matrículas escolares (INEP).
    Suporta CSV e XLSX (Sinopses).
    """
    logger.info(f"Processando matrículas de: {path_file}")
    
    try:
        if path_file.endswith(".xlsx") or path_file.endswith(".xls") or path_file.endswith(".ods"):
            # Sinopses do INEP costumam ter várias abas. Geralmente a "Municípios" ou similar.
            # Como não sabemos a aba exata, tentamos encontrar uma que tenha dados úteis.
            try:
                # Tenta aba 'Municípios' se existir
                df = pd.read_excel(path_file, sheet_name='Municípios', skiprows=10)
            except:
                df = pd.read_excel(path_file, skiprows=10)
        else:
            df = pd.read_csv(path_file, sep=None, engine='python')
        
        cols_map = {
            "Município": "municipio",
            "Municipio": "municipio",
            "NO_MUNICIPIO": "municipio",
            "Ano": "ano",
            "NU_ANO_CENSO": "ano",
            "Matriculas": "valor",
            "Matrículas": "valor",
            "Total": "valor"
        }
        df = df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns})
        
        if "municipio" in df.columns:
            df = df[df["municipio"].astype(str).str.contains(MUNICIPIO, case=False, na=False)]
            
        if "ano" not in df.columns or "valor" not in df.columns:
            # Tentar inferir ano pelo nome do arquivo/pasta
            import re
            match = re.search(r"20\d{2}", path_file)
            if match:
                df["ano"] = int(match.group())
            else:
                logger.error(f"Ano não encontrado no INEP: {path_file}")
                return pd.DataFrame()
            
            if "valor" not in df.columns:
                # Se não achou 'valor', pega a primeira coluna numérica após o município
                num_cols = df.select_dtypes(include=['number']).columns
                if not num_cols.empty:
                    df["valor"] = df[num_cols[0]]
                else:
                    logger.error(f"Fluxo INEP: Colunas numéricas não encontradas. {df.columns}")
                    return pd.DataFrame()
            
        df = df.groupby("ano")["valor"].sum().reset_index()
        df["mes"] = 0
        
        return padronizar(
            df,
            indicador="Matrículas escolares",
            categoria="Educação",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="INEP",
            manual=True
        )
    except Exception as e:
        logger.error(f"Erro ao processar INEP ({path_file}): {e}")
        return pd.DataFrame()

def run():
    logger.info("Iniciando ETL Educação INEP")
    raw_dir = DATA_DIR / "raw"
    
    # Busca recursiva por arquivos INEP/Sinopse/Matriculas
    files_by_year = {}
    import re
    
    for root, dirs, files in os.walk(raw_dir):
        for f in files:
            if any(p in f.lower() for p in ["inep", "matriculas", "sinopse"]):
                ext = f.split('.')[-1].lower()
                if ext in ['csv', 'xlsx', 'xls', 'ods']:
                    # Tentar extrair ano do nome do arquivo
                    match = re.search(r"20\d{2}", f)
                    year = match.group() if match else "unknown"
                    
                    path = os.path.join(root, f)
                    
                    if year not in files_by_year:
                        files_by_year[year] = []
                    files_by_year[year].append((ext, path))
    
    # Selecionar o melhor arquivo para cada ano (preferência: xlsx > xls > csv > ods)
    priority = {'xlsx': 0, 'xls': 1, 'csv': 2, 'ods': 3}
    final_files = []
    for year, files_list in files_by_year.items():
        # Ordena por prioridade de extensão e pega o primeiro
        best_file = sorted(files_list, key=lambda x: priority.get(x[0], 99))[0][1]
        final_files.append(best_file)

    if not final_files:
        logger.warning("Nenhum arquivo INEP encontrado em data/raw")
        return pd.DataFrame()

    all_dfs = []
    for path_file in final_files:
        df = matriculas(path_file)
        if not df.empty:
            all_dfs.append(df)
            upsert_indicators(df, indicator_key="MATRICULAS_TOTAL", source="INEP_RAW", category="Educação")
    
    if all_dfs:
        logger.info(f"ETL Educação INEP concluído com {len(all_dfs)} arquivos.")
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()

if __name__ == "__main__":
    run()
