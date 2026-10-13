"""Login of the single administrator (ADR (Architecture Decision Record) 0004): password with
Argon2 and session with JWT (JSON Web Token).

The credentials come from environment variables; there is no users table.
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
    """True if the email and password are the administrator's.

    The password is verified even if the email doesn't match, so the response time doesn't
    reveal which of the two was wrong.
    """
    # Repeats part of is_configured() so mypy knows they aren't None. No `assert`, because
    # Python skips it with `-O` (ruff rule S101).
    if not (is_configured() and settings.admin_email and settings.admin_password_hash):
        return False
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
    if not (settings.admin_email and settings.jwt_secret):
        raise RuntimeError("Administrator login is not configured")
    issued = now or datetime.now(UTC)
    claims = {
        "sub": settings.admin_email.strip().lower(),
        "iat": issued,
        "exp": issued + timedelta(days=SESSION_DAYS),
    }
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm=_ALGORITHM)


def is_valid_session(token: str) -> bool:
    """True if the token is signed with our key, hasn't expired and belongs to the current admin."""
    if not (is_configured() and settings.admin_email and settings.jwt_secret):
        return False
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
