import logging
from datetime import datetime
from typing import Optional, List, Dict

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    text,
    exc
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.sql import func

from config import DATABASE_URL, COD_IBGE, MUNICIPIO, UF

logger = logging.getLogger(__name__)

# Configuração do Engine com otimizações para Cloud (Neon/Postgres)
# pool_pre_ping=True verifica se a conexão está viva antes de usar
db_args = {}
if "postgresql" in DATABASE_URL:
    db_args = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True
    }

try:
    engine = create_engine(DATABASE_URL, future=True, **db_args)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
except Exception as e:
    logger.error(f"Falha CRÍTICA ao criar engine do banco: {e}")
    # Fallback silencioso para permitir importação em ambientes de build/CI
    engine = None
    SessionLocal = None

Base = declarative_base()

class Indicator(Base):
    """
    Tabela normalizada de indicadores socioeconômicos.
    """
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    municipality_code = Column(String(10), index=True, nullable=False)
    municipality_name = Column(String(128), nullable=False)
    uf = Column(String(2), nullable=False)
    indicator_key = Column(String(100), index=True, nullable=False)
    source = Column(String(50), index=True, nullable=False)
    year = Column(Integer, index=True, nullable=False)
    month = Column(Integer, index=True, nullable=True, default=0)
    value = Column(Float, nullable=True)
    unit = Column(String(32), nullable=True)
    category = Column(String(50), index=True, nullable=True)
    manual = Column(Boolean, default=False)
    collected_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "municipality_code", "indicator_key", "source", "year", "month",
            name="uix_indicator_unique",
        ),
    )

def init_db() -> bool:
    """Cria todas as tabelas necessárias e testa a conexão."""
    if engine is None:
        logger.error("Database Engine nulo. Verifique DATABASE_URL.")
        return False
        
    try:
        logger.info("Verificando conexão com o banco...")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("Inicializando tabelas em %s", DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'local/sqlite')
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        return False

def get_session() -> Optional[Session]:
    """Retorna uma sessão de banco com tratamento de erro."""
    if SessionLocal is None:
        return None
    return SessionLocal()

def upsert_indicators(
    df: pd.DataFrame,
    *,
    indicator_key: str,
    source: str,
    category: str = "Geral",
    municipality_code: str = COD_IBGE,
    municipality_name: str = MUNICIPIO,
    uf: str = UF,
) -> int:
    """Insere/atualiza registros de indicadores de forma idempotente."""
    if df.empty:
        return 0
        
    required_cols = {"year", "value"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Faltam colunas obrigatórias em {indicator_key}: {required_cols}")

    records = df.to_dict(orient="records")
    inserted = 0

    session = get_session()
    if session is None:
        logger.error("Não foi possível abrir sessão para upsert.")
        return 0

    try:
        for row in records:
            year = int(row["year"])
            month = int(row.get("month", 0))
            value = row.get("value")
            unit = row.get("unit")
            manual = row.get("manual", False)

            existing = (
                session.query(Indicator)
                .filter_by(
                    municipality_code=municipality_code,
                    indicator_key=indicator_key,
                    source=source,
                    year=year,
                    month=month,
                )
                .first()
            )

            if existing:
                existing.value = value
                existing.unit = unit
                existing.manual = manual
                existing.collected_at = datetime.now()
                if category != "Geral":
                    existing.category = category
            else:
                session.add(Indicator(
                    municipality_code=municipality_code,
                    municipality_name=municipality_name,
                    uf=uf,
                    indicator_key=indicator_key,
                    source=source,
                    category=category,
                    year=year,
                    month=month,
                    value=value,
                    unit=unit,
                    manual=manual,
                    collected_at=datetime.now()
                ))
                inserted += 1
        
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Falha no upsert de {indicator_key}: {e}")
        raise
    finally:
        session.close()

    logger.info("Upsert '%s' (%s): %s novos.", indicator_key, source, inserted)
    return inserted

def get_timeseries(indicator_key: str, source: Optional[str] = None) -> pd.DataFrame:
    """Recupera série histórica com tratamento para engine nulo."""
    if engine is None:
        return pd.DataFrame()

    params = {"code": COD_IBGE, "key": indicator_key}
    base_query = """
        SELECT year, month, value, unit, source
        FROM indicators
        WHERE municipality_code = :code
          AND indicator_key = :key
    """

    if source:
        base_query += " AND source = :source"
        params["source"] = source

    base_query += " ORDER BY year, month"

    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(base_query), conn, params=params)
        
        if not df.empty:
            df.rename(columns={"year": "Ano", "month": "Mes", "value": "Valor", "unit": "Unidade"}, inplace=True)
        return df
    except Exception as e:
        logger.error(f"Erro ao consultar série {indicator_key}: {e}")
        return pd.DataFrame()

def list_indicators(municipality_code: Optional[str] = None) -> List[Dict]:
    """Lista indicadores disponíveis no banco."""
    if engine is None:
        return []

    code = municipality_code or COD_IBGE
    query = text("""
        SELECT DISTINCT indicator_key, source, unit
        FROM indicators
        WHERE municipality_code = :code
        ORDER BY indicator_key, source
    """)
    try:
        with engine.connect() as conn:
            rows = conn.execute(query, {"code": code}).fetchall()
        return [{"indicator_key": r[0], "source": r[1], "unit": r[2] or ""} for r in rows]
    except Exception as e:
        logger.error(f"Erro ao listar indicadores: {e}")
        return []
