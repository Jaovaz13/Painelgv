import logging
import pandas as pd
import requests
from typing import Optional, List

from config import COD_IBGE
from database import upsert_indicators

logger = logging.getLogger(__name__)

from utils.network import safe_request

METADATA = {
    "fonte": "IBGE - SIDRA",
    "periodicidade": "Anual",
    "ultima_atualizacao": "Automática"
}

def ibge_sidra(table: str, variables: List[str], periods: str = "all", cod_ibge: Optional[str] = None) -> pd.DataFrame:
    """
    Função genérica para consultar a API do SIDRA.
    """
    cod = cod_ibge or COD_IBGE
    vars_str = ",".join(variables)
    # n6/{cod} para nível municipal
    url = (
        f"https://apisidra.ibge.gov.br/values/t/{table}"
        f"/v/{vars_str}/p/{periods}/n6/{cod}?format=json"
    )
    
    logger.info(f"Consultando SIDRA tabela {table} (vars: {vars_str}) para {cod}")
    
    data = safe_request(url)
    if not data or len(data) < 2:
        logger.warning(f"SIDRA retornou dados vazios ou inválidos para tabela {table}")
        return pd.DataFrame()
    
    return pd.DataFrame(data[1:], columns=data[0])

def transform_sidra(df: pd.DataFrame, value_col_idx: int = -1) -> pd.DataFrame:
    """
    Normaliza o DataFrame retornado pelo SIDRA.
    Geralmente colunas: D2N (Ano), V (Valor), D1N (Variável), etc.
    """
    if df.empty:
        return pd.DataFrame()

    # Tentativa de identificar colunas
    col_map = {}
    for col in df.columns:
        if col == "D2N" or (col.lower().startswith("ano") and "código" not in col.lower()):
            col_map[col] = "year"
        elif col == "V" or (col.lower().startswith("valor")):
            col_map[col] = "value"
            
    df = df.rename(columns=col_map)
    
    if "year" not in df.columns or "value" not in df.columns:
        # Fallback: tentar usar nomes padrão da API se mapeamento falhar
        if "D2N" in df.columns: df.rename(columns={"D2N": "year"}, inplace=True)
        if "V" in df.columns: df.rename(columns={"V": "value"}, inplace=True)

    if "year" not in df.columns or "value" not in df.columns:
         logger.warning("Colunas esperadas 'year' e 'value' não encontradas no retorno do SIDRA.")
         return pd.DataFrame()

    df = df[["year", "value"]].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    
    return df

def run() -> None:
    """
    Executa ETL para diversos indicadores do IBGE.
    """
    logger.info("Iniciando ETL IBGE (Múltiplos indicadores).")
    
    indicators_config = [
        {
            "key": "PIB_TOTAL",
            "table": "5938", 
            "vars": ["37"], # Valor do PIB a preços correntes
            "source": "IBGE",
            "unit": "R$ mil"
        },
        {
            "key": "PIB_PER_CAPITA",
            "table": "5938",
            "vars": ["5939"], # PIB per capita
            "source": "IBGE",
            "unit": "R$"
        },
        {
             "key": "MATRICULAS_TOTAL", # Exemplo de indicador educacional no sidra (censo escolar) ou similar
             "table": "6407", # Matrículas (exemplo, verificar tabela correta para matriculas total se nao 6407)
             "vars": ["93"], # Total de matrículas
             "source": "IBGE_EDUCACAO",
             "unit": "Unidades"
        }
        # Adicione outros conforme necessário (Empregos SIDRA podem ser defasados, CAGED é melhor)
    ]

    total_inserted = 0
    for cfg in indicators_config:
        try:
            raw = ibge_sidra(cfg["table"], cfg["vars"])
            df = transform_sidra(raw)
            if not df.empty:
                df["unit"] = cfg["unit"]
                inserted = upsert_indicators(df, indicator_key=cfg["key"], source=cfg["source"])
                total_inserted += inserted
        except Exception as e:
            logger.error(f"Falha ao processar indicador {cfg['key']}: {e}")

    logger.info(f"ETL IBGE concluído. Total registros processados: {total_inserted}")

def get_pib_timeseries():
     # Compatibilidade com código legado
     df = ibge_sidra("5938", ["37"])
     return transform_sidra(df)

