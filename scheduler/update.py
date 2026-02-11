import logging
from pathlib import Path
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from config import LOG_FORMAT, LOG_LEVEL, SCHEDULER_INTERVAL_HOURS, DATA_DIR
from database import init_db
from etl.etl_runner import run_all


logger = logging.getLogger(__name__)

# Diretório de logs
LOG_DIR = DATA_DIR.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def configure_logging() -> None:
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
    # Adicionar FileHandler para persistência
    file_handler = logging.FileHandler(LOG_DIR / "etl_scheduler.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger().addHandler(file_handler)


def etl_job() -> None:
    logger.info("="*60)
    logger.info(f"Job de atualização iniciado em {datetime.now().isoformat()}")
    init_db()
    run_all()
    logger.info(f"Job de atualização finalizado em {datetime.now().isoformat()}")


def main() -> None:
    """
    Agendador de ETL a cada SCHEDULER_INTERVAL_HOURS (padrão: 24h).

    Em produção, execute este módulo como um serviço separado do Streamlit,
    por exemplo:

        python -m scheduler.update

    ou via systemd/cron/docker.
    """
    configure_logging()

    scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        etl_job,
        "interval",
        hours=SCHEDULER_INTERVAL_HOURS,
        max_instances=1,
        coalesce=True,
    )

    # Execução imediata na inicialização
    etl_job()

    logger.info(
        "Scheduler iniciado. Intervalo de %s horas.",
        SCHEDULER_INTERVAL_HOURS,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler finalizado.")


if __name__ == "__main__":
    main()

