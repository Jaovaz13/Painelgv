"""
Módulo agregador dos processos de ETL.

Cada fonte possui um módulo próprio (ibge, rais, sebrae, etc.)
com funções `extract_*`, `transform_*` e `load_*`.
"""

import logging

from . import ibge, caged, rais, sebrae, datasus, snis, sefaz_mg, sustentabilidade
from . import educacao_inep, educacao_real


logger = logging.getLogger(__name__)


def run_all_etl() -> None:
    """
    Executa todos os ETLs de forma sequencial.
    Ideal para ser chamado pelo scheduler.
    """
    logger.info("Iniciando execução completa de ETL.")

    # IBGE / SIDRA
    try:
        ibge.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL IBGE: %s", exc)

    # CAGED
    try:
        caged.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL CAGED: %s", exc)

    # RAIS
    try:
        rais.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL RAIS: %s", exc)

    # Sebrae
    try:
        sebrae.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL Sebrae: %s", exc)

    # DataSUS
    try:
        datasus.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL DataSUS: %s", exc)

    # SNIS
    try:
        snis.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL SNIS: %s", exc)

    # SEFAZ-MG
    try:
        sefaz_mg.run()
    except NotImplementedError:
        logger.warning(
            "ETL SEFAZ-MG não implementado. Verifique necessidade de credenciais institucionais."
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL SEFAZ-MG: %s", exc)

    # Sustentabilidade
    try:
        sustentabilidade.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL Sustentabilidade: %s", exc)

    # Educação (somente dados reais em data/raw)
    try:
        educacao_inep.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL Educação (INEP/raw): %s", exc)

    try:
        # ETL complementar de educação baseado em raw (quando aplicável)
        educacao_real.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao executar ETL Educação (real/raw): %s", exc)

    logger.info("Execução completa de ETL finalizada.")

