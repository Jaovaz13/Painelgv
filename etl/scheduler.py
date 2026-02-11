import time
import logging
from datetime import datetime, timedelta
from etl.run_all import run_all

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ETL_SCHEDULER")

def job():
    logger.info("Iniciando tarefa agendada de atualização de dados...")
    try:
        run_all()
        logger.info("Tarefa de atualização concluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro durante a atualização agendada: {e}")

def run_scheduler(target_hour=2):
    """
    Executa o job a cada 24 horas, no horário alvo especificado.
    """
    logger.info(f"Agendador nativo iniciado. Atualizações diárias às {target_hour:02d}:00.")
    
    while True:
        now = datetime.now()
        # Calcula o próximo horário de execução
        next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        
        if now >= next_run:
            next_run += timedelta(days=1)
            
        wait_seconds = (next_run - now).total_seconds()
        logger.info(f"Próxima atualização em {wait_seconds/3600:.2f} horas ({next_run}).")
        
        # Dorme até o próximo horário ou check de segurança a cada 1 hora
        sleep_chunk = min(wait_seconds, 3600)
        time.sleep(sleep_chunk)
        
        # Se chegamos no horário (margem de 5 min)
        if abs((datetime.now() - next_run).total_seconds()) < 300:
            job()
            # Dorme um pouco para não rodar duas vezes no mesmo minuto
            time.sleep(600)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        job()
    else:
        # Por padrão, tenta rodar às 2 da manhã
        run_scheduler(target_hour=2)
