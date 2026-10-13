"""Contact messages and visits by UTM (Urchin Tracking Module), seen from the panel.

Against the real Postgres: each test runs in a transaction that is rolled back at the end.
"""

from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.main import app
from app.models import ContactMessage, Visit
from app.routers.admin import COOKIE_NAME
from app.services import auth

HASH_A = "a" * 64
HASH_B = "b" * 64


@pytest.fixture(autouse=True)
def admin_configurado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "admin_email", "admin@example.com")
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr("$argon2id$no-se-usa"))
    monkeypatch.setattr(settings, "jwt_secret", SecretStr("s" * 48))


@pytest.fixture
def anonimo(db_session: Session) -> Iterator[TestClient]:
    """Client without a session. The API uses the test's session and starts with empty tables."""
    db_session.execute(delete(ContactMessage))
    db_session.execute(delete(Visit))

    def sesion_del_test() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = sesion_del_test
    with TestClient(app, base_url="https://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def admin(anonimo: TestClient) -> TestClient:
    anonimo.cookies.set(COOKIE_NAME, auth.create_session_token())
    return anonimo


def mensaje(session: Session, nombre: str, creado: datetime, **campos: str) -> ContactMessage:
    item = ContactMessage(
        name=nombre,
        email="remitente@example.com",
        message="Hola",
        lang="es",
        created_at=creado,
        **campos,
    )
    session.add(item)
    session.flush()
    return item


def visita(session: Session, visitante: str, **utm: str) -> None:
    session.add(Visit(lang="es", visitor_hash=visitante, **utm))
    session.flush()


# Access without a session


@pytest.mark.parametrize(
    ("metodo", "ruta"),
    [
        ("GET", "/api/admin/messages"),
        ("PATCH", "/api/admin/messages/1"),
        ("GET", "/api/admin/visits"),
    ],
)
def test_activity_routes_without_session_respond_401(
    anonimo: TestClient, metodo: str, ruta: str
) -> None:
    response = anonimo.request(metodo, ruta, json={})

    assert response.status_code == 401
    assert response.json() == {"detail": "Log in."}


def test_without_session_does_not_mark_the_message(
    anonimo: TestClient, db_session: Session
) -> None:
    item = mensaje(db_session, "Ana", datetime(2026, 10, 1))

    anonimo.patch(f"/api/admin/messages/{item.id}", json={"read": True})

    db_session.refresh(item)
    assert item.read is False


# Messages


def test_lists_messages_from_newest_to_oldest(admin: TestClient, db_session: Session) -> None:
    mensaje(db_session, "Antiguo", datetime(2026, 10, 1))
    mensaje(
        db_session, "Nuevo", datetime(2026, 10, 2), utm_source="portal", utm_campaign="empresa-x"
    )

    response = admin.get("/api/admin/messages")

    assert response.status_code == 200
    datos = response.json()
    assert [m["name"] for m in datos] == ["Nuevo", "Antiguo"]
    assert datos[0].keys() == {
        "id",
        "created_at",
        "name",
        "email",
        "message",
        "lang",
        "utm_source",
        "utm_campaign",
        "read",
    }
    assert (datos[0]["utm_source"], datos[0]["utm_campaign"]) == ("portal", "empresa-x")
    assert datos[0]["read"] is False


def test_marks_a_message_as_read_and_unread(admin: TestClient, db_session: Session) -> None:
    item = mensaje(db_session, "Ana", datetime(2026, 10, 1))

    leido = admin.patch(f"/api/admin/messages/{item.id}", json={"read": True})
    db_session.refresh(item)
    assert leido.status_code == 200
    assert leido.json()["read"] is True
    assert item.read is True

    admin.patch(f"/api/admin/messages/{item.id}", json={"read": False})
    db_session.refresh(item)
    assert item.read is False


def test_marking_a_nonexistent_message_responds_404(admin: TestClient) -> None:
    response = admin.patch("/api/admin/messages/999999", json={"read": True})

    assert response.status_code == 404


@pytest.mark.parametrize(
    "cuerpo",
    [{}, {"read": "true"}, {"read": 1}, {"read": True, "name": "otro"}],
)
def test_marking_with_an_invalid_body_responds_422(
    admin: TestClient, db_session: Session, cuerpo: dict[str, object]
) -> None:
    item = mensaje(db_session, "Ana", datetime(2026, 10, 1))

    response = admin.patch(f"/api/admin/messages/{item.id}", json=cuerpo)

    assert response.status_code == 422


@pytest.mark.parametrize("message_id", ["0", "2147483648", "abc"])
def test_an_out_of_range_message_id_responds_422(admin: TestClient, message_id: str) -> None:
    response = admin.patch(f"/api/admin/messages/{message_id}", json={"read": True})

    assert response.status_code == 422


# Visits


def test_groups_visits_by_utm_source_and_utm_campaign(
    admin: TestClient, db_session: Session
) -> None:
    visita(db_session, HASH_A, utm_source="portal", utm_campaign="empresa-x")
    visita(db_session, HASH_A, utm_source="portal", utm_campaign="empresa-x")
    visita(db_session, HASH_B, utm_source="portal", utm_campaign="empresa-x", utm_medium="otro")
    visita(db_session, HASH_A, utm_source="portal", utm_campaign="empresa-y")
    visita(db_session, HASH_B)

    response = admin.get("/api/admin/visits")

    assert response.status_code == 200
    assert response.json() == [
        {"utm_source": "portal", "utm_campaign": "empresa-x", "visits": 3, "unique_visitors": 2},
        {"utm_source": "portal", "utm_campaign": "empresa-y", "visits": 1, "unique_visitors": 1},
        {"utm_source": None, "utm_campaign": None, "visits": 1, "unique_visitors": 1},
    ]


def test_without_visits_responds_an_empty_list(admin: TestClient) -> None:
    assert admin.get("/api/admin/visits").json() == []
