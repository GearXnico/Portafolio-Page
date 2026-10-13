"""POST /api/contact contra el Postgres real. Solo se simula el servidor de correo."""

import logging
import smtplib
from collections.abc import Callable, Iterator
from email.message import EmailMessage
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, func, select
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import settings
from app.db import SessionLocal
from app.main import MAX_BODY_BYTES, app
from app.models import ContactMessage
from app.routers.contact import contact_limiter
from app.services import contact, mail

VALIDO: dict[str, Any] = {
    "name": "Ana Pérez",
    "email": "ana@example.com",
    "message": "Hola,\nme interesa tu trabajo.",
    "lang": "es",
    "utm_source": "linkedin",
    "utm_campaign": "lanzamiento",
}


class SmtpFalso:
    """Reemplaza a smtplib.SMTP: guarda lo que se envía o falla si se le pide."""

    enviados: list[EmailMessage] = []
    error: Exception | None = None

    def __init__(self, host: str, port: int, timeout: float) -> None:
        if SmtpFalso.error is not None:
            raise SmtpFalso.error

    def __enter__(self) -> SmtpFalso:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def starttls(self, context: object) -> None:
        pass

    def login(self, user: str, password: str) -> None:
        pass

    def send_message(self, email: EmailMessage) -> None:
        SmtpFalso.enviados.append(email)


@pytest.fixture(autouse=True)
def limite_limpio() -> Iterator[None]:
    contact_limiter.reset()
    yield
    contact_limiter.reset()


Guardados = Callable[[], list[ContactMessage]]


@pytest.fixture(autouse=True)
def guardados() -> Iterator[Guardados]:
    """Lee de la base los mensajes que guardó el test, y los borra al terminar.

    La ruta hace commit, así que aquí no sirve la transacción revertida de `db_session`.
    """
    with SessionLocal() as session:
        ultimo = session.scalar(select(func.coalesce(func.max(ContactMessage.id), 0)))

    def leer() -> list[ContactMessage]:
        with SessionLocal() as session:
            consulta = select(ContactMessage).where(ContactMessage.id > ultimo)
            return list(session.scalars(consulta.order_by(ContactMessage.id)))

    yield leer
    with SessionLocal() as session:
        session.execute(delete(ContactMessage).where(ContactMessage.id > ultimo))
        session.commit()


@pytest.fixture
def smtp(monkeypatch: pytest.MonkeyPatch) -> type[SmtpFalso]:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_user", "yo@example.com")
    monkeypatch.setattr(settings, "smtp_password", SecretStr("clave"))
    monkeypatch.setattr(settings, "contact_notify_to", "yo@example.com")
    monkeypatch.setattr(smtplib, "SMTP", SmtpFalso)
    SmtpFalso.enviados = []
    SmtpFalso.error = None
    return SmtpFalso


def enviar(client: TestClient, **cambios: Any) -> Any:
    return client.post("/api/contact", json=VALIDO | cambios)


# Envío


def test_guarda_el_mensaje(client: TestClient, guardados: Guardados) -> None:
    response = enviar(client)

    assert response.status_code == 201
    assert response.json() == {"status": "ok"}
    [mensaje] = guardados()
    assert (mensaje.name, mensaje.email, mensaje.lang) == ("Ana Pérez", "ana@example.com", "es")
    assert mensaje.message == "Hola,\nme interesa tu trabajo."
    assert (mensaje.utm_source, mensaje.utm_campaign) == ("linkedin", "lanzamiento")
    assert (mensaje.read, mensaje.emailed) == (False, False)


def test_limpia_espacios_y_utm_vacias(client: TestClient, guardados: Guardados) -> None:
    response = enviar(client, name="  Ana  ", utm_source="", utm_campaign=None)

    assert response.status_code == 201
    [mensaje] = guardados()
    assert mensaje.name == "Ana"
    assert (mensaje.utm_source, mensaje.utm_campaign) == (None, None)


def test_el_contenido_se_guarda_tal_cual_sin_interpretarlo(
    client: TestClient, guardados: Guardados
) -> None:
    # La API no escapa ni ejecuta nada: guarda el texto. Quien lo muestre (React, el correo
    # de texto plano) lo escapa al mostrarlo.
    texto = "<script>alert(1)</script> ' OR 1=1; --"

    assert enviar(client, message=texto, name="<b>Ana</b>").status_code == 201

    [mensaje] = guardados()
    assert (mensaje.message, mensaje.name) == (texto, "<b>Ana</b>")


def test_acepta_los_largos_maximos(client: TestClient, guardados: Guardados) -> None:
    response = enviar(
        client,
        name="ñ" * 200,
        email="a" * 300 + "@example.com",
        message="é" * 5000,
        utm_source="s" * 200,
        utm_campaign="c" * 200,
    )

    assert response.status_code == 201
    assert len(guardados()) == 1


# Entradas inválidas


@pytest.mark.parametrize(
    "cambios",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "a" * 201},
        {"name": "Ana\r\nBcc: otro@example.com"},
        {"name": "Ana\x00"},
        {"name": "Ana\u2028Bcc"},
        {"email": "sin-arroba"},
        {"email": "ana@sin-punto"},
        {"email": "ana,otro@example.com"},
        {"email": "Ana <ana@example.com>"},
        {"email": '"ana"@example.com'},
        {"email": "ana@example.com\r\nBcc: otro@example.com"},
        {"email": "a" * 320 + "@example.com"},
        {"message": ""},
        {"message": " \n "},
        {"message": "a" * 5001},
        {"message": "nulo\x00"},
        {"message": "escape \x1b[31m"},
        {"lang": "pt"},
        {"lang": None},
        {"utm_source": "a" * 201},
        {"utm_campaign": "a\nb"},
        {"website": "x" * 2001},
        {"read": True},
        {"emailed": True},
        {"name": 123},
    ],
)
def test_rechaza_entradas_invalidas(
    client: TestClient, guardados: Guardados, cambios: dict[str, Any]
) -> None:
    response = enviar(client, **cambios)

    assert response.status_code == 422
    assert guardados() == []


@pytest.mark.parametrize("campo", ["name", "email", "message", "lang"])
def test_exige_los_campos_obligatorios(
    client: TestClient, guardados: Guardados, campo: str
) -> None:
    datos = {k: v for k, v in VALIDO.items() if k != campo}

    assert client.post("/api/contact", json=datos).status_code == 422
    assert guardados() == []


def test_rechaza_lo_que_no_es_json(client: TestClient, guardados: Guardados) -> None:
    response = client.post(
        "/api/contact", content=b"name=Ana", headers={"content-type": "text/plain"}
    )

    assert response.status_code == 422
    assert guardados() == []


def test_rechaza_un_cuerpo_demasiado_grande(client: TestClient, guardados: Guardados) -> None:
    response = client.post(
        "/api/contact",
        content=b"x" * (MAX_BODY_BYTES + 1),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert guardados() == []


def test_rechaza_un_cuerpo_sin_largo_declarado(client: TestClient) -> None:
    def por_partes() -> Iterator[bytes]:
        yield b"{}"

    response = client.post(
        "/api/contact", content=por_partes(), headers={"content-type": "application/json"}
    )

    assert response.status_code == 411


# Spam


def test_honeypot_lleno_responde_igual_pero_no_guarda(
    client: TestClient, guardados: Guardados, smtp: type[SmtpFalso]
) -> None:
    response = enviar(client, website="https://spam.example.com")

    assert response.status_code == 201
    assert response.json() == {"status": "ok"}
    assert guardados() == []
    assert smtp.enviados == []


def test_limita_a_5_mensajes_por_hora_por_ip(client: TestClient, guardados: Guardados) -> None:
    for _ in range(5):
        assert enviar(client).status_code == 201

    response = enviar(client)

    assert response.status_code == 429
    assert 3500 < int(response.headers["retry-after"]) <= 3600
    assert len(guardados()) == 5


def test_el_honeypot_tambien_cuenta_para_el_limite(client: TestClient) -> None:
    for _ in range(5):
        enviar(client, website="spam")

    assert enviar(client).status_code == 429


def test_sin_proxy_de_confianza_ignora_x_forwarded_for(client: TestClient) -> None:
    for i in range(5):
        client.post("/api/contact", json=VALIDO, headers={"x-forwarded-for": f"203.0.113.{i}"})

    response = client.post("/api/contact", json=VALIDO, headers={"x-forwarded-for": "198.51.100.1"})

    assert response.status_code == 429


def test_detras_del_proxy_de_confianza_limita_por_la_ip_del_visitante() -> None:
    # Como en producción: Caddy es el proxy de confianza (TRUSTED_PROXIES) y manda la IP real.
    detras_de_caddy: Any = ProxyHeadersMiddleware(cast(Any, app), trusted_hosts="testclient")

    with TestClient(detras_de_caddy) as client:

        def desde(ip: str) -> int:
            return client.post(
                "/api/contact", json=VALIDO, headers={"x-forwarded-for": ip}
            ).status_code

        assert [desde("203.0.113.7") for _ in range(5)] == [201] * 5
        assert desde("203.0.113.7") == 429
        assert desde("198.51.100.1") == 201


# Aviso por correo


def test_envia_el_aviso_y_marca_el_mensaje(
    client: TestClient, guardados: Guardados, smtp: type[SmtpFalso]
) -> None:
    assert enviar(client).status_code == 201

    [correo] = smtp.enviados
    assert correo["To"] == "yo@example.com"
    assert correo["Reply-To"] == "ana@example.com"
    assert correo["Subject"] == "Nuevo mensaje de contacto de Ana Pérez"
    assert correo.get_content_type() == "text/plain"
    cuerpo = correo.get_content()
    assert "me interesa tu trabajo." in cuerpo
    assert "Origen: linkedin, lanzamiento" in cuerpo
    [mensaje] = guardados()
    assert mensaje.emailed is True


@pytest.mark.parametrize(
    "error", [smtplib.SMTPAuthenticationError(535, b"no"), TimeoutError(), ConnectionRefusedError()]
)
def test_correo_fallido_igual_guarda_el_mensaje(
    client: TestClient,
    guardados: Guardados,
    smtp: type[SmtpFalso],
    caplog: pytest.LogCaptureFixture,
    error: Exception,
) -> None:
    smtp.error = error

    with caplog.at_level(logging.WARNING):
        response = enviar(client)

    assert response.status_code == 201
    [mensaje] = guardados()
    assert mensaje.emailed is False
    assert f"Could not send the notice for message {mensaje.id}" in caplog.text
    # El log no lleva datos personales.
    assert "ana@example.com" not in caplog.text and "Ana" not in caplog.text


def test_sin_smtp_configurado_guarda_y_lo_anota_en_el_log(
    client: TestClient,
    guardados: Guardados,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "smtp_host", None)

    with caplog.at_level(logging.WARNING):
        assert enviar(client).status_code == 201

    [mensaje] = guardados()
    assert mensaje.emailed is False
    assert "SMTP not configured" in caplog.text


def test_send_to_owner_sin_configurar_falla(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "smtp_password", None)

    with pytest.raises(mail.MailError):
        mail.send_to_owner(subject="x", body="y")


def test_aviso_de_un_mensaje_que_ya_no_existe_no_hace_nada(smtp: type[SmtpFalso]) -> None:
    contact.notify_new_message(2_000_000_000)

    assert smtp.enviados == []
