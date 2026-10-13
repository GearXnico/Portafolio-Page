"""API configuration, read from environment variables."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Looks for a .env in the current folder or at the repo root (if you run from api/).
    # Environment variables take priority over the file.
    # An empty variable (ADMIN_EMAIL=) counts as undefined and takes the default value.
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), extra="ignore", env_ignore_empty=True
    )

    # API user, with minimal permissions: it only reads and writes rows.
    database_url: str
    # Owner of the tables: only Alembic uses it. It is optional so that in production
    # the API process can start without knowing the owner's password.
    migration_database_url: str | None = None

    # IPs (Internet Protocol addresses) of the trusted proxies, comma-separated; accepts
    # networks (172.18.0.0/16). X-Forwarded-For is read only from them to learn the visitor's
    # real IP. Empty: the connection's IP is used, and nobody can spoof it with that header.
    trusted_proxies: str = ""

    # Email notice for each contact message (ADR (Architecture Decision Record) 0005). If any
    # is missing, the message is still saved and the log only notes that email is disabled.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    contact_notify_to: str | None = None

    # Single administrator (ADR 0004). If any is missing, login responds 503 and the panel
    # can't be used. The hash is generated with `python -m app.hash_password`.
    admin_email: str | None = None
    admin_password_hash: SecretStr | None = None
    # Signs the session cookie (JWT, JSON Web Token). At least 32 random characters; changing
    # it closes all open sessions.
    jwt_secret: SecretStr | None = Field(default=None, min_length=32)

    # Folder for the project screenshots. Caddy serves it at /media; in Docker it is a
    # volume mounted at /code/media. Relative to the folder the API runs from.
    media_dir: Path = Path("media")


settings = Settings()
