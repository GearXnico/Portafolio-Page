from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db import engine

TABLAS = {
    "profile",
    "skill",
    "experience",
    "project",
    "project_image",
    "visit",
    "contact_message",
    "visitor_salt",
}


def tablas_de_la_app() -> set[str]:
    return set(inspect(engine).get_table_names()) - {"alembic_version"}


def test_migrations_apply_and_revert() -> None:
    config = Config("alembic.ini")

    command.upgrade(config, "head")
    assert tablas_de_la_app() == TABLAS

    command.downgrade(config, "base")
    assert tablas_de_la_app() == set()

    command.upgrade(config, "head")
    assert tablas_de_la_app() == TABLAS


def test_models_match_the_migrations() -> None:
    """Fails if someone changes app/models/ and forgets to generate the migration."""
    command.check(Config("alembic.ini"))
