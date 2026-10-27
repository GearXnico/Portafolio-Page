"""Admin login: credentials, cookie, per-IP limit and access without a session."""

import getpass
import os
import re
import subprocess
import sys
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app import hash_password
from app.config import settings
from app.main import app
from app.routers.admin import COOKIE_NAME, login_limiter
from app.services import auth

EMAIL = "admin@example.com"
PASSWORD = "una clave larga de prueba"
SECRET = "s" * 48
# Hash of PASSWORD, computed once because Argon2 is slow on purpose.
HASH = auth.hash_password(PASSWORD)


@pytest.fixture(autouse=True)
def admin_configured(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(settings, "admin_email", EMAIL)
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr(HASH))
    monkeypatch.setattr(settings, "jwt_secret", SecretStr(SECRET))
    login_limiter.reset()
    yield
    login_limiter.reset()


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Over HTTPS, because the cookie is Secure and the client wouldn't send it back over HTTP.
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client


def log_in(client: TestClient, email: str = EMAIL, password: str = PASSWORD) -> Any:
    return client.post("/api/admin/login", json={"email": email, "password": password})


# Login


def test_successful_login_sets_the_session_cookie(client: TestClient) -> None:
    response = log_in(client)

    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith(f"{COOKIE_NAME}=")
    for attribute in ("httponly", "secure", "samesite=strict", "path=/api/admin", "max-age=604800"):
        assert attribute in cookie
    assert client.get("/api/admin/session").status_code == 200


def test_email_is_case_insensitive(client: TestClient) -> None:
    assert log_in(client, email="  Admin@Example.COM ").status_code == 200


@pytest.mark.parametrize(
    ("email", "password"),
    [(EMAIL, "otra clave cualquiera"), ("otro@example.com", PASSWORD), ("otro@example.com", "x")],
)
def test_bad_credentials_respond_401_without_cookie(
    client: TestClient, email: str, password: str
) -> None:
    response = log_in(client, email=email, password=password)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password."}
    assert "set-cookie" not in response.headers
    assert client.get("/api/admin/session").status_code == 401


@pytest.mark.parametrize(
    "body",
    [
        {"email": EMAIL},
        {"email": EMAIL, "password": ""},
        {"email": EMAIL, "password": "x" * 257},
        {"email": EMAIL, "password": PASSWORD, "admin": True},
    ],
)
def test_invalid_body_responds_422(client: TestClient, body: dict[str, Any]) -> None:
    assert client.post("/api/admin/login", json=body).status_code == 422


@pytest.mark.parametrize("variable", ["admin_email", "admin_password_hash", "jwt_secret"])
def test_without_configuration_login_responds_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.setattr(settings, variable, None)

    assert log_in(client).status_code == 503


def test_a_badly_copied_hash_does_not_let_anyone_in(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr("no-es-un-hash"))

    assert log_in(client).status_code == 401


def test_short_jwt_secret_is_rejected() -> None:
    with pytest.raises(ValueError, match="32"):
        type(settings)(jwt_secret="corto")


# Attempt limit


def test_blocks_after_5_failed_attempts(client: TestClient) -> None:
    for _ in range(5):
        assert log_in(client, password="mala clave").status_code == 401

    response = log_in(client)

    assert response.status_code == 429
    assert 0 < int(response.headers["retry-after"]) <= 15 * 60
    assert "set-cookie" not in response.headers


def test_a_successful_login_clears_the_failed_attempts(client: TestClient) -> None:
    for _ in range(4):
        log_in(client, password="mala clave")
    assert log_in(client).status_code == 200

    for _ in range(5):
        assert log_in(client, password="mala clave").status_code == 401
    assert log_in(client).status_code == 429


def test_block_is_by_real_ip_behind_caddy() -> None:
    behind_caddy: Any = ProxyHeadersMiddleware(cast(Any, app), trusted_hosts="testclient")
    with TestClient(behind_caddy, base_url="https://testserver") as client:
        for _ in range(5):
            response = client.post(
                "/api/admin/login",
                json={"email": EMAIL, "password": "mala clave"},
                headers={"X-Forwarded-For": "203.0.113.7"},
            )
            assert response.status_code == 401
        blocked = client.post(
            "/api/admin/login",
            json={"email": EMAIL, "password": PASSWORD},
            headers={"X-Forwarded-For": "203.0.113.7"},
        )
        other_ip = client.post(
            "/api/admin/login",
            json={"email": EMAIL, "password": PASSWORD},
            headers={"X-Forwarded-For": "198.51.100.9"},
        )

    assert blocked.status_code == 429
    assert other_ip.status_code == 200


def test_without_trusted_proxy_x_forwarded_for_does_not_change_the_ip(client: TestClient) -> None:
    for i in range(5):
        log_in_from = client.post(
            "/api/admin/login",
            json={"email": EMAIL, "password": "mala clave"},
            headers={"X-Forwarded-For": f"203.0.113.{i}"},
        )
        assert log_in_from.status_code == 401

    assert log_in(client).status_code == 429


# Session, and access to /api/admin/* without a session


def test_without_session_responds_401(client: TestClient) -> None:
    response = client.get("/api/admin/session")

    assert response.status_code == 401
    assert response.json() == {"detail": "Log in."}


def test_every_admin_route_except_login_and_logout_requires_a_session(client: TestClient) -> None:
    # Catches a new /api/admin/* route left outside the protected router.
    public_routes = {"/api/admin/login", "/api/admin/logout"}
    routes = {p: m for p, m in app.openapi()["paths"].items() if p.startswith("/api/admin")}

    assert routes.keys() >= public_routes | {"/api/admin/session"}
    for route, methods in routes.items():
        if route in public_routes:
            continue
        for method in methods:
            # Path parameters ({id}) are replaced with any value.
            response = client.request(method, re.sub(r"\{[^}]+\}", "1", route))
            assert response.status_code == 401, (method, route)


def _token(clave: str = SECRET, **changes: Any) -> str:
    """A JWT like the API's, with the requested changes (None removes the field)."""
    now = datetime.now(UTC)
    claims = {"sub": EMAIL, "iat": now, "exp": now + timedelta(days=7)} | changes
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, clave)


@pytest.mark.parametrize(
    "token",
    [
        "no-es-un-jwt",
        _token(clave="t" * 48),  # signed with another key
        _token(exp=datetime.now(UTC) - timedelta(seconds=1)),  # expired
        _token(sub="otro@example.com"),  # for another email
        _token(exp=None),  # no expiry
        jwt.encode({"sub": EMAIL}, key=None, algorithm="none"),  # unsigned
    ],
)
def test_invalid_session_responds_401(client: TestClient, token: str) -> None:
    client.cookies.set(COOKIE_NAME, token)

    assert client.get("/api/admin/session").status_code == 401


def test_removing_the_configuration_closes_the_session(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_in(client)
    monkeypatch.setattr(settings, "jwt_secret", None)

    assert client.get("/api/admin/session").status_code == 401


def test_without_configuration_no_token_is_created(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret", None)

    with pytest.raises(RuntimeError):
        auth.create_session_token()


def test_changing_the_email_closes_the_session(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_in(client)
    monkeypatch.setattr(settings, "admin_email", "nuevo@example.com")

    assert client.get("/api/admin/session").status_code == 401


def test_logout_deletes_the_cookie(client: TestClient) -> None:
    log_in(client)

    response = client.post("/api/admin/logout")

    assert response.status_code == 204
    assert 'admin_session=""' in response.headers["set-cookie"]
    assert client.get("/api/admin/session").status_code == 401


def test_logout_without_session_responds_204(client: TestClient) -> None:
    assert client.post("/api/admin/logout").status_code == 204


# Command to generate the hash


def _responses(monkeypatch: pytest.MonkeyPatch, *texts: str) -> None:
    pending = list(texts)
    monkeypatch.setattr(getpass, "getpass", lambda prompt: pending.pop(0))


def test_command_prints_a_hash_that_verifies(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _responses(monkeypatch, PASSWORD, PASSWORD)

    assert hash_password.main() == 0

    line = capsys.readouterr().out.strip()
    assert line.startswith("ADMIN_PASSWORD_HASH='$argon2id$") and line.endswith("'")
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr(line.split("'")[1]))
    assert auth.verify_credentials(EMAIL, PASSWORD)
    assert PASSWORD not in line


@pytest.mark.parametrize(
    ("first", "second"),
    [("corta", "corta"), (PASSWORD, "otra clave distinta"), ("x" * 257,) * 2],
)
def test_command_rejects_short_or_mismatched_passwords(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], first: str, second: str
) -> None:
    _responses(monkeypatch, first, second)

    assert hash_password.main() == 1
    assert capsys.readouterr().out == ""


def test_command_runs_without_the_api_configuration(tmp_path: Path) -> None:
    # On the server it runs in a bare container, before .env has the hash.
    env = {k: v for k, v in os.environ.items() if not k.endswith("DATABASE_URL")}
    result = subprocess.run(
        [sys.executable, "-c", "import app.hash_password"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_empty_variables_count_as_undefined(monkeypatch: pytest.MonkeyPatch) -> None:
    # That's how they are in .env.example and compose.yml: the API still has to start.
    for variable in ("ADMIN_EMAIL", "ADMIN_PASSWORD_HASH", "JWT_SECRET"):
        monkeypatch.setenv(variable, "")

    empty = type(settings)()

    assert (empty.admin_email, empty.admin_password_hash, empty.jwt_secret) == (None, None, None)
