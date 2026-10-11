"""Conexión a Postgres con SQLAlchemy."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_session() -> Iterator[Session]:
    """Entrega una sesión por request y la cierra al terminar."""
    with SessionLocal() as session:
        yield session
