from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import get_session
from app.main import app


def test_health_responde_200_con_la_base_arriba(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_responde_503_si_la_base_no_contesta(client: TestClient) -> None:
    # Una conexión real a un puerto donde no hay nada escuchando.
    engine = create_engine("postgresql+psycopg://nadie:nada@127.0.0.1:1/nada")

    def session_sin_base() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_sin_base

    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "La base de datos no responde"}
