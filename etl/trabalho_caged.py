import pandas as pd
import logging
from etl.utils import padronizar
from config import MUNICIPIO, UF

logger = logging.getLogger(__name__)

def saldo_empregos():
    """
    Placeholder para o saldo de empregos (CAGED).
    A API pública do Portal da Transparência retorna agregados nacionais.
    Para dados municipais, recomenda-se o uso de CSV manual do portal PDET.
    """
    # url = "https://api.portaldatransparencia.gov.br/api-de-dados/caged"
    logger.info("CAGED: Aguardando integração com arquivos manuais para dados municipais.")
    return pd.DataFrame()

def run():
    logger.info("Iniciando ETL CAGED")
    df = saldo_empregos()
    if not df.empty:
        # Quando implementado, upsert aqui
        pass
    else:
        logger.info("Nota metodológica: Para dados do CAGED em nível municipal, utilize o carregamento manual.")

if __name__ == "__main__":
    run()
