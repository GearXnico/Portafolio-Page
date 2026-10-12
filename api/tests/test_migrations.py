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


def test_las_migraciones_se_aplican_y_revierten() -> None:
    config = Config("alembic.ini")

    command.upgrade(config, "head")
    assert tablas_de_la_app() == TABLAS

    command.downgrade(config, "base")
    assert tablas_de_la_app() == set()

    command.upgrade(config, "head")
    assert tablas_de_la_app() == TABLAS


def test_los_modelos_coinciden_con_las_migraciones() -> None:
    """Falla si alguien cambia app/models/ y olvida generar la migración."""
    command.check(Config("alembic.ini"))
