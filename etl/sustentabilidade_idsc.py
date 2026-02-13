import pandas as pd
import logging
import os
from etl.utils import padronizar
from config import MUNICIPIO, UF, DATA_DIR
from database import upsert_indicators

logger = logging.getLogger(__name__)

def idsc(path_file):
    """
    Processa dados do IDSC-BR. Suporta CSV e XLSX.
    """
    logger.info(f"Processando IDSC: {path_file}")
    
    try:
        # Inferir ano pelo nome do arquivo
        import re
        year_match = re.search(r"20\d{2}", path_file)
        file_year = int(year_match.group()) if year_match else None

        if path_file.endswith(".xlsx") or path_file.endswith(".xls"):
            xl = pd.ExcelFile(path_file)
            sheet_name = xl.sheet_names[0]
            # Prioridade de abas: Séries Temporais > Todos os Dados > IDSC-BR
            prioridades = ["Séries Temporais", "Series Temporais", "Todos os Dados", "IDSC-BR"]
            for p in prioridades:
                for s in xl.sheet_names:
                    if p.lower() in s.lower():
                        sheet_name = s
                        break
                else: continue
                break
            
            logger.info(f"Lendo aba: {sheet_name}")
            df = pd.read_excel(path_file, sheet_name=sheet_name)
        else:
            df = pd.read_csv(path_file, sep=None, engine='python', encoding='utf-8')
            
        cols_map = {
            "Município": "municipio",
            "Municipio": "municipio",
            "Cidade": "municipio",
            "NM_Municipio": "municipio",
            "COD_MUN": "cod_ibge",
            "Ano": "ano",
            "Year": "ano",
            "ano": "ano"
        }
        df = df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns})
        
        # Procurar coluna de valor (Score Geral, Pontuação Geral, IDSC-BR...)
        if "valor" not in df.columns:
            import re
            score_patterns = [r"Score Geral", r"Pontuação Geral", r"IDSC-BR.*", r"Indice.*"]
            for col in df.columns:
                 for pattern in score_patterns:
                     if re.match(pattern, col, re.IGNORECASE):
                         df = df.rename(columns={col: "valor"})
                         break
                 if "valor" in df.columns: break
        
        # Se não tem coluna de ano, usa o do arquivo
        if "ano" not in df.columns and file_year:
            df["ano"] = file_year
            
        # Filtrar GV
        # Pode estar em cod_ibge, municipio ou NM_Municipio
        if "cod_ibge" in df.columns:
            df = df[df["cod_ibge"].astype(str).str.contains("3127701")]
        elif "municipio" in df.columns:
            df = df[df["municipio"].astype(str).str.contains(MUNICIPIO, case=False, na=False)]
        elif "NM_Municipio" in df.columns:
            df = df[df["NM_Municipio"].astype(str).str.contains(MUNICIPIO, case=False, na=False)]
            
        if "ano" not in df.columns or "valor" not in df.columns:
            logger.error(f"Colunas obrigatórias não encontradas no IDSC ({path_file}). Colunas: {df.columns}")
            return pd.DataFrame()
            
        df = df[["ano", "valor"]].drop_duplicates()
        df["mes"] = 0
        
        return padronizar(
            df,
            indicador="IDSC-BR",
            categoria="Sustentabilidade",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="IDSC-BR",
            manual=True
        )
    except Exception as e:
        logger.error(f"Erro ao processar IDSC ({path_file}): {e}")
        return pd.DataFrame()

def run():
    logger.info("Iniciando ETL Sustentabilidade IDSC")
    raw_dir = DATA_DIR / "raw"
    files = [f for f in os.listdir(raw_dir) if "idsc" in f.lower()]
    
    if not files:
        logger.warning("Nenhum arquivo IDSC encontrado em data/raw")
        return pd.DataFrame()

    all_dfs = []
    for f in files:
        path_file = str(raw_dir / f)
        df = idsc(path_file)
        if not df.empty:
            all_dfs.append(df)
            upsert_indicators(df, indicator_key="IDSC_GERAL", source="IDSC", category="Sustentabilidade")
    
    if all_dfs:
        logger.info(f"ETL IDSC concluído com {len(all_dfs)} arquivos.")
        return pd.concat(all_dfs)
    return pd.DataFrame()

if __name__ == "__main__":
    run()
