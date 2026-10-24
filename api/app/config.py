from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # An empty variable (ADMIN_EMAIL=) counts as unset.
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), extra="ignore", env_ignore_empty=True
    )

    # API user, with minimal permissions: it only reads and writes rows.
    database_url: str
    # Owner of the tables: only Alembic uses it. It is optional so that in production
    # the API process can start without knowing the owner's password.
    migration_database_url: str | None = None

    # Comma-separated IPs or networks allowed to set X-Forwarded-For. Empty: the connection's
    # IP is used, so nobody can spoof it with that header.
    trusted_proxies: str = ""

    # Contact notice. If any is missing, messages are still saved, without the email.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    contact_notify_to: str | None = None

    # If any is missing, login responds 503. Hash with `python -m app.hash_password`.
    admin_email: str | None = None
    admin_password_hash: SecretStr | None = None
    # At least 32 random characters; changing it closes all open sessions.
    jwt_secret: SecretStr | None = Field(default=None, min_length=32)

    # Caddy serves this folder at /media; in Docker it is a volume mounted at /code/media.
    media_dir: Path = Path("media")


settings = Settings()
