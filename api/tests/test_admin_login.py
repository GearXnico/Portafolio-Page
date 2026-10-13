"""Admin login (ADR 0004): credentials, cookie, per-IP limit and access without a session."""

import getpass
import re
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
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

CORREO = "admin@example.com"
CLAVE = "una clave larga de prueba"
SECRETO = "s" * 48
# Hash of CLAVE, computed once because Argon2 is slow on purpose.
HASH = auth.hash_password(CLAVE)


@pytest.fixture(autouse=True)
def admin_configurado(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(settings, "admin_email", CORREO)
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr(HASH))
    monkeypatch.setattr(settings, "jwt_secret", SecretStr(SECRETO))
    login_limiter.reset()
    yield
    login_limiter.reset()


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Over HTTPS, because the cookie is Secure and the client wouldn't send it back over HTTP.
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client


def entrar(client: TestClient, email: str = CORREO, password: str = CLAVE) -> Any:
    return client.post("/api/admin/login", json={"email": email, "password": password})


# Login


def test_successful_login_sets_the_session_cookie(client: TestClient) -> None:
    response = entrar(client)

    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith(f"{COOKIE_NAME}=")
    for atributo in ("httponly", "secure", "samesite=strict", "path=/api/admin", "max-age=604800"):
        assert atributo in cookie
    assert client.get("/api/admin/session").status_code == 200


def test_email_is_case_insensitive(client: TestClient) -> None:
    assert entrar(client, email="  Admin@Example.COM ").status_code == 200


@pytest.mark.parametrize(
    ("email", "password"),
    [(CORREO, "otra clave cualquiera"), ("otro@example.com", CLAVE), ("otro@example.com", "x")],
)
def test_bad_credentials_respond_401_without_cookie(
    client: TestClient, email: str, password: str
) -> None:
    response = entrar(client, email=email, password=password)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password."}
    assert "set-cookie" not in response.headers
    assert client.get("/api/admin/session").status_code == 401


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"email": CORREO},
        {"email": CORREO, "password": ""},
        {"email": CORREO, "password": "x" * 257},
        {"email": CORREO, "password": CLAVE, "admin": True},
    ],
)
def test_invalid_body_responds_422(client: TestClient, cuerpo: dict[str, Any]) -> None:
    assert client.post("/api/admin/login", json=cuerpo).status_code == 422


@pytest.mark.parametrize("variable", ["admin_email", "admin_password_hash", "jwt_secret"])
def test_without_configuration_login_responds_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.setattr(settings, variable, None)

    assert entrar(client).status_code == 503


def test_a_badly_copied_hash_does_not_let_anyone_in(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr("no-es-un-hash"))

    assert entrar(client).status_code == 401


def test_short_jwt_secret_is_rejected() -> None:
    with pytest.raises(ValueError, match="32"):
        type(settings)(jwt_secret="corto")


# Attempt limit


def test_blocks_after_5_failed_attempts(client: TestClient) -> None:
    for _ in range(5):
        assert entrar(client, password="mala clave").status_code == 401

    response = entrar(client)

    assert response.status_code == 429
    assert 0 < int(response.headers["retry-after"]) <= 15 * 60
    assert "set-cookie" not in response.headers


def test_a_successful_login_clears_the_failed_attempts(client: TestClient) -> None:
    for _ in range(4):
        entrar(client, password="mala clave")
    assert entrar(client).status_code == 200

    for _ in range(5):
        assert entrar(client, password="mala clave").status_code == 401
    assert entrar(client).status_code == 429


def test_block_is_by_real_ip_behind_caddy() -> None:
    detras_de_caddy: Any = ProxyHeadersMiddleware(cast(Any, app), trusted_hosts="testclient")
    with TestClient(detras_de_caddy, base_url="https://testserver") as client:
        for _ in range(5):
            response = client.post(
                "/api/admin/login",
                json={"email": CORREO, "password": "mala clave"},
                headers={"X-Forwarded-For": "203.0.113.7"},
            )
            assert response.status_code == 401
        bloqueada = client.post(
            "/api/admin/login",
            json={"email": CORREO, "password": CLAVE},
            headers={"X-Forwarded-For": "203.0.113.7"},
        )
        otra_ip = client.post(
            "/api/admin/login",
            json={"email": CORREO, "password": CLAVE},
            headers={"X-Forwarded-For": "198.51.100.9"},
        )

    assert bloqueada.status_code == 429
    assert otra_ip.status_code == 200


def test_without_trusted_proxy_x_forwarded_for_does_not_change_the_ip(client: TestClient) -> None:
    for i in range(5):
        entrar_con_ip = client.post(
            "/api/admin/login",
            json={"email": CORREO, "password": "mala clave"},
            headers={"X-Forwarded-For": f"203.0.113.{i}"},
        )
        assert entrar_con_ip.status_code == 401

    assert entrar(client).status_code == 429


# Session, and access to /api/admin/* without a session


def test_without_session_responds_401(client: TestClient) -> None:
    response = client.get("/api/admin/session")

    assert response.status_code == 401
    assert response.json() == {"detail": "Log in."}


def test_every_admin_route_except_login_and_logout_requires_a_session(client: TestClient) -> None:
    # Catches a new /api/admin/* route left outside the protected router.
    publicas = {"/api/admin/login", "/api/admin/logout"}
    rutas = {p: m for p, m in app.openapi()["paths"].items() if p.startswith("/api/admin")}

    assert rutas.keys() >= publicas | {"/api/admin/session"}
    for ruta, metodos in rutas.items():
        if ruta in publicas:
            continue
        for metodo in metodos:
            # Path parameters ({id}) are replaced with any value.
            response = client.request(metodo, re.sub(r"\{[^}]+\}", "1", ruta))
            assert response.status_code == 401, (metodo, ruta)


def _token(clave: str = SECRETO, **cambios: Any) -> str:
    """A JWT like the API's, with the requested changes (None removes the field)."""
    ahora = datetime.now(UTC)
    claims = {"sub": CORREO, "iat": ahora, "exp": ahora + timedelta(days=7)} | cambios
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, clave)


@pytest.mark.parametrize(
    "token",
    [
        "no-es-un-jwt",
        _token(clave="t" * 48),  # signed with another key
        _token(exp=datetime.now(UTC) - timedelta(seconds=1)),  # expired
        _token(sub="otro@example.com"),  # for another email
        _token(exp=None),  # no expiry
        jwt.encode({"sub": CORREO}, key=None, algorithm="none"),  # unsigned
    ],
)
def test_invalid_session_responds_401(client: TestClient, token: str) -> None:
    client.cookies.set(COOKIE_NAME, token)

    assert client.get("/api/admin/session").status_code == 401


def test_removing_the_configuration_closes_the_session(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    entrar(client)
    monkeypatch.setattr(settings, "jwt_secret", None)

    assert client.get("/api/admin/session").status_code == 401


def test_without_configuration_no_token_is_created(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret", None)

    with pytest.raises(RuntimeError):
        auth.create_session_token()


def test_changing_the_email_closes_the_session(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    entrar(client)
    monkeypatch.setattr(settings, "admin_email", "nuevo@example.com")

    assert client.get("/api/admin/session").status_code == 401


def test_logout_deletes_the_cookie(client: TestClient) -> None:
    entrar(client)

    response = client.post("/api/admin/logout")

    assert response.status_code == 204
    assert 'admin_session=""' in response.headers["set-cookie"]
    assert client.get("/api/admin/session").status_code == 401


def test_logout_without_session_responds_204(client: TestClient) -> None:
    assert client.post("/api/admin/logout").status_code == 204


# Command to generate the hash


def _respuestas(monkeypatch: pytest.MonkeyPatch, *textos: str) -> None:
    pendientes = list(textos)
    monkeypatch.setattr(getpass, "getpass", lambda prompt: pendientes.pop(0))


def test_command_prints_a_hash_that_verifies(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _respuestas(monkeypatch, CLAVE, CLAVE)

    assert hash_password.main() == 0

    linea = capsys.readouterr().out.strip()
    assert linea.startswith("ADMIN_PASSWORD_HASH='$argon2id$") and linea.endswith("'")
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr(linea.split("'")[1]))
    assert auth.verify_credentials(CORREO, CLAVE)
    assert CLAVE not in linea


@pytest.mark.parametrize(
    ("primera", "segunda"), [("corta", "corta"), (CLAVE, "otra clave distinta"), ("x" * 257,) * 2]
)
def test_command_rejects_short_or_mismatched_passwords(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], primera: str, segunda: str
) -> None:
    _respuestas(monkeypatch, primera, segunda)

    assert hash_password.main() == 1
    assert capsys.readouterr().out == ""


def test_empty_variables_count_as_undefined(monkeypatch: pytest.MonkeyPatch) -> None:
    # That's how they are in .env.example and compose.yml: the API still has to start.
    for variable in ("ADMIN_EMAIL", "ADMIN_PASSWORD_HASH", "JWT_SECRET"):
        monkeypatch.setenv(variable, "")

    vacia = type(settings)()

    assert (vacia.admin_email, vacia.admin_password_hash, vacia.jwt_secret) == (None, None, None)
