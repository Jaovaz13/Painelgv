import pandas as pd
import logging
from etl.utils import padronizar
from config import COD_IBGE, MUNICIPIO, UF
from database import upsert_indicators

from utils.network import safe_request

logger = logging.getLogger(__name__)

def populacao_por_idade_sexo():
    """
    Busca população por faixa etária e sexo do IBGE SIDRA.
    Tabela 6579 - População residente, por grupos de idade e sexo.
    """
    # Exemplo IBGE – População por sexo e idade (conforme sugestão do usuário)
    # n6 é nível municipal
    url = f"https://apisidra.ibge.gov.br/values/t/6579/n6/{COD_IBGE}"
    
    try:
        data = safe_request(url)
        
        if not data or not isinstance(data, list) or len(data) < 2:
            logger.warning("Dados demográficos não encontrados ou formato inválido.")
            return pd.DataFrame()
            
        df = pd.DataFrame(data[1:])
        # V: Valor, D3C: Ano
        df = df.rename(columns={"V": "valor", "D3C": "ano"})
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
        df["mes"] = 0
        
        df = df[["valor", "ano", "mes"]].dropna()
        
        return padronizar(
            df,
            indicador="População por faixa etária e sexo",
            categoria="Demografia",
            municipio=MUNICIPIO,
            uf=UF,
            fonte="IBGE/SIDRA",
            manual=False
        )
    except Exception as e:
        logger.error(f"Erro ao buscar dados demográficos: {e}")
        return pd.DataFrame()

def run():
    logger.info("Iniciando ETL Demografia")
    df = populacao_por_idade_sexo()
    if not df.empty:
        upsert_indicators(df, indicator_key="POPULACAO_DETALHADA", source="IBGE/SIDRA", category="Demografia")
        logger.info("ETL Demografia concluído com sucesso.")
    else:
        logger.warning("Nenhum dado demográfico processado.")
    return df

if __name__ == "__main__":
    run()
