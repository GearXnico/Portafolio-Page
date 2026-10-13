import pytest

from app.config import Settings


def test_api_starts_without_the_owner_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://api:clave@db/app")
    monkeypatch.delenv("MIGRATION_DATABASE_URL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.migration_database_url is None
