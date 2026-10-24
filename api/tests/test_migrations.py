from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db import engine

TABLES = {
    "profile",
    "skill",
    "experience",
    "project",
    "project_image",
    "visit",
    "contact_message",
    "visitor_salt",
}


def app_tables() -> set[str]:
    return set(inspect(engine).get_table_names()) - {"alembic_version"}


def test_migrations_apply_and_revert() -> None:
    config = Config("alembic.ini")

    command.upgrade(config, "head")
    assert app_tables() == TABLES

    command.downgrade(config, "base")
    assert app_tables() == set()

    command.upgrade(config, "head")
    assert app_tables() == TABLES


def test_models_match_the_migrations() -> None:
    """Fails if someone changes app/models/ and forgets to generate the migration."""
    command.check(Config("alembic.ini"))
