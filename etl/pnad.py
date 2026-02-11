import logging
import pandas as pd
from config import COD_IBGE
from database import upsert_indicators
from utils.network import safe_request

METADATA = {
    "fonte": "IBGE - PNAD Contínua (Proxy)",
    "periodicidade": "Trimestral/Anual",
    "ultima_atualizacao": "Automática"
}

logger = logging.getLogger(__name__)

def pnad_desemprego(cod_mun: str = COD_IBGE) -> pd.DataFrame:
    """
    Coleta Taxa de Desocupação (Proxy) ou Pessoas Desocupadas.
    Tabela 4099 do SIDRA (PNAD Contínua).
    Nota: PNAD nem sempre tem dado municipal. Se falhar, tenta outra fonte ou retorna vazio.
    """
    # Tabela 4099: Taxa de desocupação...
    # Var 4099: Taxa de desocupação
    url = (
        "https://apisidra.ibge.gov.br/values/t/4099"
        f"/v/4099/p/all/n6/{cod_mun}?format=json"
    )
    
    logger.info(f"Consultando PNAD (Proxy Desemprego) para {cod_mun}")
    
    data = safe_request(url)
    
    if not data or len(data) < 2:
        logger.warning("PNAD retornou vazio ou sem dados para este município.")
        return pd.DataFrame()
        
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def transform_pnad(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    
    # Colunas esperadas: D2N (Trimestre/Ano), V (Valor)
    # PNAD geralmente é trimestral "202304" ou periodos como "1º t"
    
    col_valor = "V" if "V" in df.columns else "Valor"
    col_data = "D2N" if "D2N" in df.columns else "Trimestre Móvel"
    
    # Tenta também coluna alternativa de ano
    col_ano = None
    for c in ["D3N", "Ano", "ano", "D2C"]:
        if c in df.columns:
            col_ano = c
            break
    
    if col_valor not in df.columns:
        return pd.DataFrame()
        
    df["value"] = pd.to_numeric(df[col_valor], errors="coerce")
    
    # Tentar extrair ano de diferentes formas
    if col_ano and col_ano in df.columns:
        # Usando coluna de ano direta
        df["year"] = pd.to_numeric(df[col_ano].astype(str).str.extract(r'(\d{4})')[0], errors="coerce")
    elif col_data in df.columns:
        # Tentar extrair ano do período (formato "202304" ou "1º trimestre 2023")
        extracted = df[col_data].astype(str).str.extract(r'(\d{4})')
        if not extracted[0].isna().all():
            df["year"] = pd.to_numeric(extracted[0], errors="coerce")
        else:
            logger.warning(f"Não foi possível extrair ano da coluna {col_data}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()
    
    # Remove linhas sem ano válido
    df = df.dropna(subset=["year"])
    if df.empty:
        return pd.DataFrame()
    
    df["year"] = df["year"].astype(int)
    
    # Agregar média anual (já que é taxa)
    grouped = df.groupby("year")["value"].mean().reset_index()
    grouped["unit"] = "%"
    
    return grouped

def run() -> None:
    logger.info("Iniciando ETL PNAD (Proxy Desemprego).")
    raw = pnad_desemprego()
    df = transform_pnad(raw)
    
    if not df.empty:
        inserted = upsert_indicators(
            df, 
            indicator_key="TAXA_DESEMPREGO_PROXY", 
            source="IBGE_PNAD", 
            category="Trabalho & Renda"
        )
        logger.info(f"ETL PNAD concluído. Registros: {inserted}")
    else:
        logger.warning("Nenhum dado PNAD processado.")
