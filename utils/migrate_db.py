"""
Script de utilitário para migrar dados do banco SQLite local 
para um banco de dados PostgreSQL na nuvem (Neon/Supabase/etc).

Uso:
1. Configure a variável de ambiente DATABASE_DESTINO (URL do Postgres)
2. Rode: python utils/migrate_db.py
"""
import os
import sys
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

# Adicionar diretório raiz ao path para importar database.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine as engine_local, Indicator as IndicatorLocal

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MIGRACAO_DB")

def migrate():
    # URL do banco de destino (Nuvem)
    # Exemplo: "postgresql+psycopg2://user:password@host:5432/dbname"
    dest_url = os.getenv("DATABASE_URL_NUVEM")
    
    if not dest_url or "sqlite" in dest_url:
        logger.error("Var DATABASE_URL_NUVEM não configurada ou aponta para SQLite. Configure uma URL Postgres.")
        return

    logger.info("Conectando ao banco de destino...")
    try:
        engine_dest = create_engine(dest_url)
        SessionDest = sessionmaker(bind=engine_dest)
        
        # Criar tabelas no destino
        logger.info("Criando tabelas no destino...")
        from database import Base
        Base.metadata.create_all(engine_dest)
        
        # Abrir sessões
        session_local = sessionmaker(bind=engine_local)()
        session_dest = SessionDest()
        
        # Buscar dados locais
        logger.info("Lendo dados locais...")
        records = session_local.query(IndicatorLocal).all()
        logger.info(f"Encontrados {len(records)} registros para migrar.")
        
        # Migrar dados
        count = 0
        migrated = 0
        for rec in records:
            count += 1
            # Verificar se já existe no destino
            exists = session_dest.query(IndicatorLocal).filter_by(
                municipality_code=rec.municipality_code,
                indicator_key=rec.indicator_key,
                source=rec.source,
                year=rec.year,
                month=rec.month
            ).first()

            if not exists:
                # Criar novo objeto para o destino
                new_rec = IndicatorLocal(
                    municipality_code=rec.municipality_code,
                    municipality_name=rec.municipality_name,
                    uf=rec.uf,
                    indicator_key=rec.indicator_key,
                    source=rec.source,
                    year=rec.year,
                    month=rec.month,
                    value=rec.value,
                    unit=rec.unit,
                    category=rec.category,
                    manual=rec.manual,
                    collected_at=rec.collected_at
                )
                session_dest.add(new_rec)
                migrated += 1
            
            # Commit em lotes
            if count % 100 == 0:
                session_dest.commit()
                logger.info(f"Progresso: {count} processados, {migrated} migrados...")
        
        session_dest.commit()
        logger.info(f"🎉 Migração concluída! Processados: {count}, Novos: {migrated}")
        
    except Exception as e:
        logger.error(f"Erro durante a migração: {e}")
    finally:
        session_local.close()
        if 'session_dest' in locals():
            session_dest.close()

if __name__ == "__main__":
    migrate()
