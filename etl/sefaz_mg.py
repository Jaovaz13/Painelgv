import logging
import pandas as pd
import requests
import io
from config import COD_IBGE
from database import upsert_indicators

logger = logging.getLogger(__name__)

def vaf_mg_csv(ano: int) -> pd.DataFrame:
    """
    Baixa CSV anual do VAF da Fazenda MG.
    """
    url = f"https://www.fazenda.mg.gov.br/empresas/vaf/municipios/{ano}.csv"
    logger.info(f"Baixando VAF MG para {ano}: {url}")
    try:
        resp = requests.get(url, timeout=60, verify=False) # verify=False pois sites gov muitas vezes tem certs invalidos
        if resp.status_code == 200:
            # Tentar ler CSV (sep pode variar ;) ou ,)
            try:
                return pd.read_csv(io.StringIO(resp.text), sep=";", encoding="latin1")
            except:
                return pd.read_csv(io.StringIO(resp.text), sep=",", encoding="latin1")
        return pd.DataFrame()
    except Exception as e:
        logger.warning(f"Erro ao baixar VAF MG ({ano}): {e}")
        return pd.DataFrame()

def transform_vaf(df: pd.DataFrame, cod_ibge: str) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    
    # Limpar nomes de colunas
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Filtrar pelo município (cod_ibge ou nome)
    # Geralmente tem coluna 'municipio' ou 'cod'
    # Ajuste fino necessário conforme layout real
    
    # Exemplo genérico:
    filtered = pd.DataFrame()
    if "municipio" in df.columns:
        filtered = df[df["municipio"].astype(str).str.contains(cod_ibge[-4:] or "x", case=False)] # Tenta match parcial
    
    if filtered.empty: return pd.DataFrame()

    # Assumindo coluna 'vaf' ou 'valor'
    val_col = next((c for c in df.columns if "vaf" in c or "valor" in c), None)
    
    if val_col:
        val = pd.to_numeric(filtered[val_col].iloc[0], errors="coerce")
        return pd.DataFrame([{
            "year": 0, # O ano vem do parametro da funcao principal
            "value": val,
            "unit": "VAF (R$)"
        }])
        
    return pd.DataFrame()

def run() -> None:
    logger.info("Iniciando ETL SEFAZ-MG (VAF).")
    import datetime
    anos = range(2020, datetime.date.today().year) # Ultimos anos
    
    total = 0
    for ano in anos:
        raw = vaf_mg_csv(ano)
        df = transform_vaf(raw, COD_IBGE)
        if not df.empty:
            df["year"] = ano
            upsert_indicators(df, indicator_key="VAF_MUNICIPAL", source="SEFAZ_MG")
            total += 1
            
    logger.info(f"ETL SEFAZ-MG concluído. Registros: {total}")

