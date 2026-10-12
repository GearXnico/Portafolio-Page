"""Login del administrador (ADR 0004): credenciales, cookie, límite por IP y acceso sin sesión."""

import getpass
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
# Hash de CLAVE, calculado una vez porque Argon2 es lento a propósito.
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
    # Por HTTPS, porque la cookie es Secure y el cliente no la devolvería por HTTP.
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client


def entrar(client: TestClient, email: str = CORREO, password: str = CLAVE) -> Any:
    return client.post("/api/admin/login", json={"email": email, "password": password})


# Login


def test_login_correcto_deja_la_cookie_de_sesion(client: TestClient) -> None:
    response = entrar(client)

    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith(f"{COOKIE_NAME}=")
    for atributo in ("httponly", "secure", "samesite=strict", "path=/api/admin", "max-age=604800"):
        assert atributo in cookie
    assert client.get("/api/admin/session").status_code == 200


def test_el_correo_no_distingue_mayusculas(client: TestClient) -> None:
    assert entrar(client, email="  Admin@Example.COM ").status_code == 200


@pytest.mark.parametrize(
    ("email", "password"),
    [(CORREO, "otra clave cualquiera"), ("otro@example.com", CLAVE), ("otro@example.com", "x")],
)
def test_credenciales_malas_responden_401_sin_cookie(
    client: TestClient, email: str, password: str
) -> None:
    response = entrar(client, email=email, password=password)

    assert response.status_code == 401
    assert response.json() == {"detail": "Correo o contraseña incorrectos."}
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
def test_cuerpo_invalido_responde_422(client: TestClient, cuerpo: dict[str, Any]) -> None:
    assert client.post("/api/admin/login", json=cuerpo).status_code == 422


@pytest.mark.parametrize("variable", ["admin_email", "admin_password_hash", "jwt_secret"])
def test_sin_configuracion_el_login_responde_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.setattr(settings, variable, None)

    assert entrar(client).status_code == 503


def test_un_hash_mal_copiado_no_deja_entrar(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr("no-es-un-hash"))

    assert entrar(client).status_code == 401


def test_jwt_secret_corto_no_se_acepta() -> None:
    with pytest.raises(ValueError, match="32"):
        type(settings)(jwt_secret="corto")


# Límite de intentos


def test_bloquea_tras_5_intentos_fallidos(client: TestClient) -> None:
    for _ in range(5):
        assert entrar(client, password="mala clave").status_code == 401

    response = entrar(client)

    assert response.status_code == 429
    assert 0 < int(response.headers["retry-after"]) <= 15 * 60
    assert "set-cookie" not in response.headers


def test_un_login_correcto_borra_los_intentos_fallidos(client: TestClient) -> None:
    for _ in range(4):
        entrar(client, password="mala clave")
    assert entrar(client).status_code == 200

    for _ in range(5):
        assert entrar(client, password="mala clave").status_code == 401
    assert entrar(client).status_code == 429


def test_el_bloqueo_es_por_ip_real_detras_de_caddy() -> None:
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


def test_sin_proxy_de_confianza_x_forwarded_for_no_cambia_la_ip(client: TestClient) -> None:
    for i in range(5):
        entrar_con_ip = client.post(
            "/api/admin/login",
            json={"email": CORREO, "password": "mala clave"},
            headers={"X-Forwarded-For": f"203.0.113.{i}"},
        )
        assert entrar_con_ip.status_code == 401

    assert entrar(client).status_code == 429


# Sesión y acceso sin sesión a /api/admin/*


def test_sin_sesion_responde_401(client: TestClient) -> None:
    response = client.get("/api/admin/session")

    assert response.status_code == 401
    assert response.json() == {"detail": "Inicia sesión."}


def _token(clave: str = SECRETO, **cambios: Any) -> str:
    """Un JWT como el de la API, con los cambios pedidos (None quita el campo)."""
    ahora = datetime.now(UTC)
    claims = {"sub": CORREO, "iat": ahora, "exp": ahora + timedelta(days=7)} | cambios
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, clave)


@pytest.mark.parametrize(
    "token",
    [
        "no-es-un-jwt",
        _token(clave="t" * 48),  # firmado con otra clave
        _token(exp=datetime.now(UTC) - timedelta(seconds=1)),  # vencido
        _token(sub="otro@example.com"),  # de otro correo
        _token(exp=None),  # sin vencimiento
        jwt.encode({"sub": CORREO}, key=None, algorithm="none"),  # sin firma
    ],
)
def test_sesion_invalida_responde_401(client: TestClient, token: str) -> None:
    client.cookies.set(COOKIE_NAME, token)

    assert client.get("/api/admin/session").status_code == 401


def test_quitar_la_configuracion_cierra_la_sesion(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    entrar(client)
    monkeypatch.setattr(settings, "jwt_secret", None)

    assert client.get("/api/admin/session").status_code == 401


def test_cambiar_el_correo_cierra_la_sesion(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    entrar(client)
    monkeypatch.setattr(settings, "admin_email", "nuevo@example.com")

    assert client.get("/api/admin/session").status_code == 401


def test_logout_borra_la_cookie(client: TestClient) -> None:
    entrar(client)

    response = client.post("/api/admin/logout")

    assert response.status_code == 204
    assert 'admin_session=""' in response.headers["set-cookie"]
    assert client.get("/api/admin/session").status_code == 401


def test_logout_sin_sesion_responde_204(client: TestClient) -> None:
    assert client.post("/api/admin/logout").status_code == 204


# Comando para generar el hash


def _respuestas(monkeypatch: pytest.MonkeyPatch, *textos: str) -> None:
    pendientes = list(textos)
    monkeypatch.setattr(getpass, "getpass", lambda prompt: pendientes.pop(0))


def test_el_comando_imprime_un_hash_que_verifica(
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
def test_el_comando_rechaza_claves_cortas_o_distintas(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], primera: str, segunda: str
) -> None:
    _respuestas(monkeypatch, primera, segunda)

    assert hash_password.main() == 1
    assert capsys.readouterr().out == ""


def test_variables_vacias_cuentan_como_no_definidas(monkeypatch: pytest.MonkeyPatch) -> None:
    # Así quedan en .env.example y en compose.yml: la API tiene que arrancar igual.
    for variable in ("ADMIN_EMAIL", "ADMIN_PASSWORD_HASH", "JWT_SECRET"):
        monkeypatch.setenv(variable, "")

    vacia = type(settings)()

    assert (vacia.admin_email, vacia.admin_password_hash, vacia.jwt_secret) == (None, None, None)
