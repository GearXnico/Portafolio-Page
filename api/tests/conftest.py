"""Fixtures compartidas. Los tests usan el Postgres real de DATABASE_URL, sin mocks de la base."""

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def migraciones_aplicadas() -> None:
    """Deja la base en la última migración antes de correr cualquier test."""
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Sesión en una transacción que se revierte al final: cada test parte con la base limpia.

    Los errores de una restricción solo revierten un savepoint, así que el test puede seguir
    usando la sesión después de un IntegrityError.
    """
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()
