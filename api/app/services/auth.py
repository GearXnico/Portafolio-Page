"""Login del administrador único (ADR 0004): contraseña con Argon2 y sesión con JWT.

Las credenciales vienen de variables de entorno; no hay tabla de usuarios.
"""

import hmac
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import settings

SESSION_DAYS = 7
_ALGORITHM = "HS256"
_hasher = PasswordHasher()


def is_configured() -> bool:
    return bool(settings.admin_email and settings.admin_password_hash and settings.jwt_secret)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_credentials(email: str, password: str) -> bool:
    """True si el correo y la contraseña son los del administrador.

    La contraseña se verifica aunque el correo no calce, para que el tiempo de respuesta no
    revele cuál de los dos estaba mal.
    """
    if not is_configured():
        return False
    assert settings.admin_email and settings.admin_password_hash
    email_ok = hmac.compare_digest(
        email.strip().lower().encode(), settings.admin_email.strip().lower().encode()
    )
    password_ok: bool
    try:
        password_ok = _hasher.verify(settings.admin_password_hash.get_secret_value(), password)
    except VerificationError, InvalidHashError:
        password_ok = False
    return email_ok and password_ok


def create_session_token(now: datetime | None = None) -> str:
    assert settings.admin_email and settings.jwt_secret
    issued = now or datetime.now(UTC)
    claims = {
        "sub": settings.admin_email.strip().lower(),
        "iat": issued,
        "exp": issued + timedelta(days=SESSION_DAYS),
    }
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm=_ALGORITHM)


def is_valid_session(token: str) -> bool:
    """True si el token está firmado con nuestra clave, no venció y es del administrador actual."""
    if not is_configured():
        return False
    assert settings.admin_email and settings.jwt_secret
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]},
        )
    except jwt.InvalidTokenError:
        return False
    return bool(claims["sub"] == settings.admin_email.strip().lower())
