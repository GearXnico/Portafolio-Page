"""POST /api/contact against the real Postgres. Only the mail server is faked."""

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

VALID: dict[str, Any] = {
    "name": "Ana Pérez",
    "email": "ana@example.com",
    "message": "Hola,\nme interesa tu trabajo.",
    "lang": "es",
    "utm_source": "linkedin",
    "utm_campaign": "lanzamiento",
}


class FakeSmtp:
    """Replaces smtplib.SMTP: stores what is sent, or fails when asked to."""

    sent: list[EmailMessage] = []
    error: Exception | None = None

    def __init__(self, host: str, port: int, timeout: float) -> None:
        if FakeSmtp.error is not None:
            raise FakeSmtp.error

    def __enter__(self) -> FakeSmtp:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def starttls(self, context: object) -> None:
        pass

    def login(self, user: str, password: str) -> None:
        pass

    def send_message(self, email: EmailMessage) -> None:
        FakeSmtp.sent.append(email)


@pytest.fixture(autouse=True)
def trimmed_limit() -> Iterator[None]:
    contact_limiter.reset()
    yield
    contact_limiter.reset()


Saved = Callable[[], list[ContactMessage]]


@pytest.fixture(autouse=True)
def saved() -> Iterator[Saved]:
    """Read from the database the messages the test saved, and delete them at the end.

    The route commits, so the rolled-back transaction of `db_session` doesn't work here.
    """
    with SessionLocal() as session:
        last = session.scalar(select(func.coalesce(func.max(ContactMessage.id), 0)))

    def read() -> list[ContactMessage]:
        with SessionLocal() as session:
            query = select(ContactMessage).where(ContactMessage.id > last)
            return list(session.scalars(query.order_by(ContactMessage.id)))

    yield read
    with SessionLocal() as session:
        session.execute(delete(ContactMessage).where(ContactMessage.id > last))
        session.commit()


@pytest.fixture
def smtp(monkeypatch: pytest.MonkeyPatch) -> type[FakeSmtp]:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_user", "yo@example.com")
    monkeypatch.setattr(settings, "smtp_password", SecretStr("clave"))
    monkeypatch.setattr(settings, "contact_notify_to", "yo@example.com")
    monkeypatch.setattr(smtplib, "SMTP", FakeSmtp)
    FakeSmtp.sent = []
    FakeSmtp.error = None
    return FakeSmtp


def send(client: TestClient, **changes: Any) -> Any:
    return client.post("/api/contact", json=VALID | changes)


# Sending


def test_saves_the_message(client: TestClient, saved: Saved) -> None:
    response = send(client)

    assert response.status_code == 201
    assert response.json() == {"status": "ok"}
    [message] = saved()
    assert (message.name, message.email, message.lang) == ("Ana Pérez", "ana@example.com", "es")
    assert message.message == "Hola,\nme interesa tu trabajo."
    assert (message.utm_source, message.utm_campaign) == ("linkedin", "lanzamiento")
    assert (message.read, message.emailed) == (False, False)


def test_trims_spaces_and_empty_utm(client: TestClient, saved: Saved) -> None:
    response = send(client, name="  Ana  ", utm_source="", utm_campaign=None)

    assert response.status_code == 201
    [message] = saved()
    assert message.name == "Ana"
    assert (message.utm_source, message.utm_campaign) == (None, None)


def test_content_is_saved_as_is_without_interpreting_it(client: TestClient, saved: Saved) -> None:
    # The API doesn't escape or run anything: it saves the text. Whoever shows it (React, the
    # plain-text email) escapes it when showing it.
    text = "<script>alert(1)</script> ' OR 1=1; --"

    assert send(client, message=text, name="<b>Ana</b>").status_code == 201

    [message] = saved()
    assert (message.message, message.name) == (text, "<b>Ana</b>")


def test_accepts_the_maximum_lengths(client: TestClient, saved: Saved) -> None:
    response = send(
        client,
        name="ñ" * 200,
        email="a" * 300 + "@example.com",
        message="é" * 5000,
        utm_source="s" * 200,
        utm_campaign="c" * 200,
    )

    assert response.status_code == 201
    assert len(saved()) == 1


# Invalid input


@pytest.mark.parametrize(
    "changes",
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
def test_rejects_invalid_input(client: TestClient, saved: Saved, changes: dict[str, Any]) -> None:
    response = send(client, **changes)

    assert response.status_code == 422
    assert saved() == []


@pytest.mark.parametrize("field", ["name", "email", "message", "lang"])
def test_requires_the_mandatory_fields(client: TestClient, saved: Saved, field: str) -> None:
    data = {k: v for k, v in VALID.items() if k != field}

    assert client.post("/api/contact", json=data).status_code == 422
    assert saved() == []


def test_rejects_what_is_not_json(client: TestClient, saved: Saved) -> None:
    response = client.post(
        "/api/contact", content=b"name=Ana", headers={"content-type": "text/plain"}
    )

    assert response.status_code == 422
    assert saved() == []


def test_rejects_a_body_that_is_too_large(client: TestClient, saved: Saved) -> None:
    response = client.post(
        "/api/contact",
        content=b"x" * (MAX_BODY_BYTES + 1),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert saved() == []


def test_rejects_a_body_without_declared_length(client: TestClient) -> None:
    def in_chunks() -> Iterator[bytes]:
        yield b"{}"

    response = client.post(
        "/api/contact", content=in_chunks(), headers={"content-type": "application/json"}
    )

    assert response.status_code == 411


# Spam


def test_filled_honeypot_responds_the_same_but_saves_nothing(
    client: TestClient, saved: Saved, smtp: type[FakeSmtp]
) -> None:
    response = send(client, website="https://spam.example.com")

    assert response.status_code == 201
    assert response.json() == {"status": "ok"}
    assert saved() == []
    assert smtp.sent == []


def test_limits_to_5_messages_per_hour_per_ip(client: TestClient, saved: Saved) -> None:
    for _ in range(5):
        assert send(client).status_code == 201

    response = send(client)

    assert response.status_code == 429
    assert 3500 < int(response.headers["retry-after"]) <= 3600
    assert len(saved()) == 5


def test_honeypot_also_counts_toward_the_limit(client: TestClient) -> None:
    for _ in range(5):
        send(client, website="spam")

    assert send(client).status_code == 429


def test_without_trusted_proxy_ignores_x_forwarded_for(client: TestClient) -> None:
    for i in range(5):
        client.post("/api/contact", json=VALID, headers={"x-forwarded-for": f"203.0.113.{i}"})

    response = client.post("/api/contact", json=VALID, headers={"x-forwarded-for": "198.51.100.1"})

    assert response.status_code == 429


def test_behind_the_trusted_proxy_limits_by_the_visitor_ip() -> None:
    # As in production: Caddy is the trusted proxy (TRUSTED_PROXIES) and sends the real IP.
    behind_caddy: Any = ProxyHeadersMiddleware(cast(Any, app), trusted_hosts="testclient")

    with TestClient(behind_caddy) as client:

        def since(ip: str) -> int:
            return client.post(
                "/api/contact", json=VALID, headers={"x-forwarded-for": ip}
            ).status_code

        assert [since("203.0.113.7") for _ in range(5)] == [201] * 5
        assert since("203.0.113.7") == 429
        assert since("198.51.100.1") == 201


# Email notice


def test_sends_the_notice_and_marks_the_message(
    client: TestClient, saved: Saved, smtp: type[FakeSmtp]
) -> None:
    assert send(client).status_code == 201

    [email] = smtp.sent
    assert email["To"] == "yo@example.com"
    assert email["Reply-To"] == "ana@example.com"
    assert email["Subject"] == "Nuevo mensaje de contacto de Ana Pérez"
    assert email.get_content_type() == "text/plain"
    body = email.get_content()
    assert "me interesa tu trabajo." in body
    assert "Origen: linkedin, lanzamiento" in body
    [message] = saved()
    assert message.emailed is True


@pytest.mark.parametrize(
    "error", [smtplib.SMTPAuthenticationError(535, b"no"), TimeoutError(), ConnectionRefusedError()]
)
def test_failed_email_still_saves_the_message(
    client: TestClient,
    saved: Saved,
    smtp: type[FakeSmtp],
    caplog: pytest.LogCaptureFixture,
    error: Exception,
) -> None:
    smtp.error = error

    with caplog.at_level(logging.WARNING):
        response = send(client)

    assert response.status_code == 201
    [message] = saved()
    assert message.emailed is False
    assert f"Could not send the notice for message {message.id}" in caplog.text
    # The log carries no personal data.
    assert "ana@example.com" not in caplog.text and "Ana" not in caplog.text


def test_without_smtp_configured_saves_and_notes_it_in_the_log(
    client: TestClient,
    saved: Saved,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "smtp_host", None)

    with caplog.at_level(logging.WARNING):
        assert send(client).status_code == 201

    [message] = saved()
    assert message.emailed is False
    assert "SMTP not configured" in caplog.text


def test_send_to_owner_fails_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "smtp_password", None)

    with pytest.raises(mail.MailError):
        mail.send_to_owner(subject="x", body="y")


def test_notice_for_a_message_that_no_longer_exists_does_nothing(smtp: type[FakeSmtp]) -> None:
    contact.notify_new_message(2_000_000_000)

    assert smtp.sent == []
