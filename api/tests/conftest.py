"""Shared fixtures. Tests use the real Postgres from DATABASE_URL, with no database mocks."""

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
    """Bring the database to the latest migration before running any test."""
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Session in a transaction that is rolled back at the end: each test starts with a clean DB.

    Constraint errors only roll back a savepoint, so the test can keep using the session after
    an IntegrityError.
    """
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()
