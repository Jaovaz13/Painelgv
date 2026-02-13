import pandas as pd
import logging
import os
import sys

# Permitir importações da raiz
sys.path.insert(0, os.getcwd())

from etl.utils import padronizar
from config import MUNICIPIO, UF, DATA_DIR
from database import upsert_indicators

logger = logging.getLogger(__name__)

def empresas_ativas(path_csv, indicador: str, unidade: str):
    """
    Processa dados do Sebrae.
    Suporta formato antigo e formato DataSebrae (Country ID, Municipality ID, Year, Workers).
    """
    logger.info(f"Processando arquivo Sebrae: {path_csv}")

    try:
        # Tentar detectar separador
        try:
            df = pd.read_csv(path_csv, sep=None, engine='python')
        except Exception:
            df = pd.read_csv(path_csv)

        cols_map = {
            "Município": "municipio",
            "Municipio": "municipio",
            "Municipality": "municipio",
            "NM_MUNICIPIO": "municipio",
            "Ano": "ano",
            "Year": "ano",
            "Empresas": "valor",
            "Empresas ativas": "valor",
            "Workers": "valor",
            "Empregados total": "valor",
            "Number workers": "valor",
            "Estabelecimentos": "valor",
            "Establishments": "valor",
        }

        # Renomeamento cuidadoso para evitar colunas duplicadas
        for k, v in cols_map.items():
            if k in df.columns and v not in df.columns:
                df = df.rename(columns={k: v})
            elif k in df.columns and v in df.columns:
                # Se já existe a coluna destino, apenas remove a coluna de origem redundante
                df = df.drop(columns=[k])
        
        # Remover colunas duplicadas se houver (caso existissem de antes)
        df = df.loc[:, ~df.columns.duplicated()]

        if "municipio" in df.columns:
            # Filtrar por GV (ID 3127701 ou nome)
            if "Municipality ID" in df.columns:
                df = df[df["Municipality ID"].astype(str) == "3127701"]
            else:
                df = df[df["municipio"].astype(str).str.contains(MUNICIPIO, case=False, na=False)]

        if "ano" not in df.columns or "valor" not in df.columns:
            logger.error(f"Colunas obrigatórias não encontradas no Sebrae. Colunas: {df.columns}")
            return pd.DataFrame()

        df = df.groupby("ano")["valor"].sum().reset_index()
        df["mes"] = 0
        df["unit"] = unidade

        return padronizar(
            df,
            indicador=indicador,
            categoria="Negócios",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="DataSebrae",
            manual=True,
        )
    except Exception as e:
        logger.error(f"Erro ao processar arquivo Sebrae: {e}")
        return pd.DataFrame()

def run():
    logger.info("Iniciando ETL Negócios Sebrae")
    raw_dir = DATA_DIR / "raw"
    # Buscar arquivos que começam com empregados ou estabelecimentos ou evolucao ou contém sebrae
    search_patterns = ["sebrae", "empresas", "empregados", "estabelecimentos", "evolucao"]
    files = [f for f in os.listdir(raw_dir) if any(p in f.lower() for p in search_patterns)]
    
    if not files:
        logger.warning("Nenhum arquivo Sebrae encontrado em data/raw")
        return pd.DataFrame()

    all_dfs = []
    for f in files:
        path_file = str(raw_dir / f)
        file_lower = f.lower()
        indicador = "Empresas/Empregos (Sebrae)"
        unit = "Unidades"
        key = "EMPRESAS_ATIVAS"

        if "empregados" in file_lower or "workers" in file_lower:
            indicador = "Empregados (Sebrae)"
            unit = "Trabalhadores"
            key = "EMPREGOS_SEBRAE"
        elif "estabelecimentos" in file_lower:
            indicador = "Estabelecimentos (Sebrae)"
            unit = "Estabelecimentos"
            key = "ESTABELECIMENTOS_SEBRAE"
        elif "mei" in file_lower:
            indicador = "MEI (Sebrae)"
            unit = "MEIs"
            key = "EMPREENDEDORES_MEI"

        df = empresas_ativas(path_file, indicador, unit)
        if not df.empty:
            all_dfs.append(df)
            upsert_indicators(df, indicator_key=key, source="SEBRAE", category="Negócios")
    
    if all_dfs:
        logger.info(f"ETL Negócios Sebrae concluído com {len(all_dfs)} arquivos.")
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()

if __name__ == "__main__":
    run()
