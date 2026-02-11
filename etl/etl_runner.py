import logging
import time

from database import init_db
from etl import (
    ibge, caged, datasus, snis, sefaz_mg, sustentabilidade,
    pnad, manual_sources, demograficos,
    caged_novo_manual, dados_manuais_extras, saude,
    sebrae, seeg, mapbiomas, esf, empregos,
    mei, salarios, sebrae_real, educacao_real
)
from etl import educacao_inep
from config import LOG_LEVEL, LOG_FORMAT

# Configuração básica de logging se rodar direto
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def run_all() -> None:
    """Executa todos os módulos de ETL seqüencialmente."""
    start = time.time()
    logger.info("Iniciando carga completa de dados (ETL Runner).")
    
    init_db()
    
    modules = [
        ("IBGE", ibge),
        ("DEMOGRAFICOS", demograficos),
        ("CAGED_API", caged),
        ("CAGED_NOVO_MANUAL", caged_novo_manual),
        ("MANUAIS_EXTRAS", dados_manuais_extras),
        ("SAUDE_MANUAL", saude),
        ("DATASUS", datasus),
        ("SNIS", snis),
        ("SEFAZ_MG", sefaz_mg),
        ("IDSC", sustentabilidade),
        # EDUCAÇÃO: por política institucional, usar exclusivamente arquivos reais em data/raw
        ("EDUCACAO_INEP_RAW", educacao_inep),
        ("EDUCACAO_REAL_RAW", educacao_real),
        ("PNAD", pnad),
        ("MANUAIS_BASE", manual_sources),
        ("SEBRAE", sebrae),
        ("SEEG", seeg),
        ("MAPBIOMAS", mapbiomas),
        ("ESF", esf),
        ("EMPREGOS", empregos),
        ("MEI", mei),
        ("SALARIOS", salarios),
        ("SEBRAE_REAL", sebrae_real)
    ]

    for name, module in modules:
        try:
            logger.info(f"--- Executando ETL {name} ---")
            module.run()
        except Exception as e:
            logger.exception(f"Falha no módulo {name}: {e}")

    elapsed = time.time() - start
    logger.info("Carga completa finalizada em %.2f segundos.", elapsed)

if __name__ == "__main__":
    run_all()
