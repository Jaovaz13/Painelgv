import pandas as pd
import logging
from etl.utils import padronizar
from config import COD_IBGE, MUNICIPIO, UF
from database import upsert_indicators
from utils.network import safe_request

logger = logging.getLogger(__name__)

def pib_municipal():
    """
    Busca o PIB Municipal e Setorial do IBGE SIDRA.
    """
    mapping = {
        "1": ("PIB_AGROPECUARIA", "Valor adicionado bruto a preços correntes da agropecuária"),
        "2": ("PIB_INDUSTRIA", "Valor adicionado bruto a preços correntes da indústria"),
        "3": ("PIB_SERVICOS", "Valor adicionado bruto a preços correntes dos serviços"),
        "4": ("PIB_ADM_PUBLICA", "Valor adicionado bruto a preços correntes da administração, defesa, educação e saúde públicas e seguridade social"),
        "7": ("PIB_TOTAL", "Produto Interno Bruto a preços correntes")
    }
    
    results = []
    for var_id, (key, name) in mapping.items():
        url = f"https://apisidra.ibge.gov.br/values/t/5938/v/{var_id}/p/all/n6/{COD_IBGE}"
        try:
            data = safe_request(url, headers={'User-Agent': 'Mozilla/5.0'})
            if not data or not isinstance(data, list) or len(data) < 2:
                continue
                
            header = data[0]
            rows = data[1:]
            df_subset = pd.DataFrame(rows, columns=header)
            
            df_subset = df_subset.rename(columns={"V": "valor", "D3C": "ano"})
            df_subset["valor"] = pd.to_numeric(df_subset["valor"], errors="coerce")
            df_subset["ano"] = pd.to_numeric(df_subset["ano"], errors="coerce")
            df_subset["mes"] = 0
            df_subset = df_subset[["valor", "ano", "mes"]].dropna()
            
            df_pad = padronizar(
                df_subset,
                indicador=key,
                categoria="Economia",
                municipio=MUNICIPIO,
                uf=UF,
                fonte="IBGE",
                manual=False
            )
            results.append((df_pad, key))
        except Exception as e:
            logger.error(f"Erro ao buscar variável {var_id} do PIB: {e}")
            
    return results

def run():
    logger.info("Iniciando ETL PIB Municipal e Setorial")
    results = pib_municipal()
    final_dfs = []
    for df, key in results:
        if not df.empty:
            upsert_indicators(df, indicator_key=key, source="IBGE", category="Economia")
            final_dfs.append(df)
            logger.info(f"ETL {key} concluído.")
    
    if not results:
        logger.warning("Nenhum dado de PIB processado.")
        return pd.DataFrame()
    return pd.concat(final_dfs) if final_dfs else pd.DataFrame()

if __name__ == "__main__":
    run()
