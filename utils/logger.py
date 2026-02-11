import logging
import sys
from pathlib import Path
from config import LOGS_DIR, LOG_LEVEL, LOG_FORMAT

def setup_logger(name: str) -> logging.Logger:
    """
    Configura um logger padronizado para o projeto Painel GV.
    Envia logs para o console e para um arquivo rotativo.
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Evita duplicação de handlers se o logger já estiver configurado
    if not logger.handlers:
        formatter = logging.Formatter(LOG_FORMAT)

        # Handler para Console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Handler para Arquivo
        try:
            log_file = LOGS_DIR / "painel_gv.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Se falhar a criação do arquivo (ex: sem permissão em cloud), 
            # apenas continua com o console_handler
            print(f"Aviso: Não foi possível criar arquivo de log: {e}")

    return logger
