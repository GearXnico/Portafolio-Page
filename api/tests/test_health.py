from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import get_session
from app.main import app


def test_health_responds_200_with_the_database_up(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_responds_503_if_the_database_does_not_answer(client: TestClient) -> None:
    # A real connection to a port where nothing is listening.
    engine = create_engine("postgresql+psycopg://nadie:nada@127.0.0.1:1/nada")

    def session_sin_base() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_sin_base

    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "The database is not responding"}
