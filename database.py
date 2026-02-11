import logging
from datetime import datetime
from typing import Optional

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
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.sql import func

from config import DATABASE_URL, COD_IBGE, MUNICIPIO, UF


logger = logging.getLogger(__name__)


engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


class Indicator(Base):
    """
    Tabela normalizada de indicadores.
    Cada fonte (IBGE, RAIS, etc.) grava aqui usando uma chave de indicador.
    """

    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    municipality_code = Column(String(10), index=True, nullable=False)
    municipality_name = Column(String(128), nullable=False)
    uf = Column(String(2), nullable=False)

    # Ex.: "PIB_TOTAL", "EMPREGOS_CAGED", etc.
    indicator_key = Column(String(100), index=True, nullable=False)
    source = Column(String(50), index=True, nullable=False)

    year = Column(Integer, index=True, nullable=False)
    month = Column(Integer, index=True, nullable=True, default=0)
    value = Column(Float, nullable=True)
    unit = Column(String(32), nullable=True)
    
    category = Column(String(50), index=True, nullable=True)
    manual = Column(Boolean, default=False)
    collected_at = Column(DateTime, default=datetime.now)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "municipality_code",
            "indicator_key",
            "source",
            "year",
            "month",
            name="uix_indicator_unique",
        ),
    )


def init_db() -> None:
    """Cria todas as tabelas necessárias."""
    logger.info("Inicializando banco de dados em %s", DATABASE_URL)
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Retorna uma sessão de banco."""
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
    """
    Insere/atualiza registros de indicadores de forma idempotente.

    Espera um DataFrame com colunas: ["year", "value", "unit"].
    """
    required_cols = {"year", "value"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"DataFrame para {indicator_key} deve conter colunas {required_cols}, recebeu: {df.columns}"
        )

    records = df.to_dict(orient="records")
    inserted = 0

    with get_session() as session:
        for row in records:
            year = int(row["year"])
            month = int(row.get("month", 0))
            value = row.get("value")
            unit = row.get("unit")
            manual = row.get("manual", False)

            existing: Optional[Indicator] = (
                session.query(Indicator)
                .filter_by(
                    municipality_code=municipality_code,
                    indicator_key=indicator_key,
                    source=source,
                    year=year,
                    month=month,
                )
                .one_or_none()
            )

            if existing:
                existing.value = value
                existing.unit = unit
                existing.manual = manual
                existing.collected_at = datetime.now()
                if category != "Geral":
                    existing.category = category
            else:
                session.add(
                    Indicator(
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
                    )
                )
                session.flush()  # Garante que a próxima iteração veja este registro
                inserted += 1

        session.commit()

    logger.info(
        "Upsert de indicador '%s' (fonte=%s) concluiu com %s novos registros.",
        indicator_key,
        source,
        inserted,
    )
    return inserted


def get_timeseries(indicator_key: str, source: Optional[str] = None) -> pd.DataFrame:
    """
    Recupera série histórica de um indicador para o município padrão.
    """
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

    with engine.connect() as conn:
        df = pd.read_sql(text(base_query), conn, params=params)

    df.rename(columns={"year": "Ano", "month": "Mes", "value": "Valor", "unit": "Unidade"}, inplace=True)
    return df


def list_indicators(municipality_code: Optional[str] = None) -> list[dict]:
    """
    Lista indicadores disponíveis no banco para o município.
    Retorna lista de dicts com indicator_key, source, unit.
    """
    code = municipality_code or COD_IBGE
    query = text("""
        SELECT DISTINCT indicator_key, source, unit
        FROM indicators
        WHERE municipality_code = :code
        ORDER BY indicator_key, source
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"code": code}).fetchall()
    return [
        {"indicator_key": r[0], "source": r[1], "unit": r[2] or ""}
        for r in rows
    ]

