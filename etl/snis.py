import logging
import pandas as pd
import requests
import io
from config import COD_IBGE
from database import upsert_indicators

logger = logging.getLogger(__name__)

def snis_agua_csv(ano: int) -> pd.DataFrame:
    """
    Baixa CSV anual de Água do SNIS.
    """
    url = f"https://www.gov.br/mdr/pt-br/snis/arquivos/{ano}_agua.csv"
    logger.info(f"Baixando SNIS Água para {ano}: {url}")
    try:
        resp = requests.get(url, timeout=120, verify=False)
        if resp.status_code == 200:
            # SNIS costuma ser separado por ponto-e-vírgula e encoding latin1 ou utf-8
            try:
                return pd.read_csv(io.StringIO(resp.text), sep=";", encoding="latin1")
            except:
                return pd.read_csv(io.StringIO(resp.text), sep=";", encoding="utf-8")
        return pd.DataFrame()
    except Exception as e:
        logger.warning(f"Erro ao baixar SNIS Água ({ano}): {e}")
        return pd.DataFrame()

def transform_snis(df: pd.DataFrame, cod_ibge: str) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    
    # SNIS geralmente tem coluna 'Código do Município' ou 'GE006' (Codigo IBGE)
    # Vamos normalizar colunas
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Tentar filtrar pelo codigo
    filtered = pd.DataFrame()
    # Procurar coluna que pareça código IBGE
    col_cod = next((c for c in df.columns if "im006" in c or "codigo" in c or "municipio" in c), None)
    
    if col_cod:
        # Filtrar pelo código IBGE (6 ou 7 digitos)
        filtered = df[df[col_cod].astype(str).str.contains(cod_ibge[:6])] 
        
    if filtered.empty: return pd.DataFrame()
    
    # Extrair indicadores chave (Ex: AG001 - População atendida, etc.)
    # Exemplo: IN055 - Índice de atendimento total de água (fictício/exemplo, usar reais se souber) or AG001
    indicadores = []
    
    target_cols = {
        "ag001": "AGUA_POP_ATENDIDA",
        "in055": "AGUA_ATENDIMENTO"
    }
    
    for col, key in target_cols.items():
        if col in filtered.columns:
            val = pd.to_numeric(filtered[col].iloc[0], errors="coerce")
            indicadores.append({
                "year": 0, # Definido pelo loop externo
                "value": val,
                "unit": "Habitantes" if "pop" in key.lower() else "%",
                "key": key
            })
            
    return pd.DataFrame(indicadores)

def run() -> None:
    logger.info("Iniciando ETL SNIS.")
    import datetime
    anos = range(2020, datetime.date.today().year)
    
    total = 0
    for ano in anos:
        raw = snis_agua_csv(ano)
        df_ind = transform_snis(raw, COD_IBGE)
        
        if not df_ind.empty:
            df_ind["year"] = ano
            for _, row in df_ind.iterrows():
                upsert_indicators(
                    pd.DataFrame([row]), 
                    indicator_key=row["key"], 
                    source="SNIS"
                )
                total += 1
                
    logger.info(f"ETL SNIS concluído. Registros: {total}")

