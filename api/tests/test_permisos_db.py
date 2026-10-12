"""La API se conecta con un usuario de permisos mínimos: puede tocar filas, no el esquema.

Si estos tests fallan, DATABASE_URL probablemente apunta al dueño de las tablas
en vez de al usuario de la API (ver README, "Base de datos: dos usuarios").
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db import engine


def ejecutar(sql: str) -> None:
    with engine.connect() as connection:
        connection.execute(text(sql))
        connection.rollback()


def test_el_usuario_de_la_api_no_es_superusuario_ni_dueno() -> None:
    with engine.connect() as connection:
        rol = connection.execute(
            text(
                "SELECT rolsuper, rolcreatedb, rolcreaterole, rolbypassrls"
                " FROM pg_roles WHERE rolname = current_user"
            )
        ).one()
        dueno = connection.execute(
            text("SELECT tableowner FROM pg_tables WHERE tablename = 'project'")
        ).scalar_one()
        usuario = connection.execute(text("SELECT current_user")).scalar_one()

    assert tuple(rol) == (False, False, False, False)
    assert dueno != usuario


@pytest.mark.parametrize(
    "sql",
    [
        "CREATE TABLE intrusa (id int)",
        "DROP TABLE project",
        "TRUNCATE project",
        "ALTER TABLE project ADD COLUMN intrusa int",
        "CREATE INDEX intruso ON project (title_es)",
    ],
)
def test_el_usuario_de_la_api_no_puede_cambiar_el_esquema(sql: str) -> None:
    with pytest.raises(ProgrammingError, match="InsufficientPrivilege|permission denied|must be"):
        ejecutar(sql)


def test_el_usuario_de_la_api_lee_y_escribe_filas() -> None:
    with engine.connect() as connection:
        connection.execute(text("INSERT INTO skill (name, category) VALUES ('Python', 'language')"))
        connection.execute(text("UPDATE skill SET position = 1"))
        assert connection.execute(text("SELECT count(*) FROM skill")).scalar_one() >= 1
        connection.execute(text("DELETE FROM skill"))
        connection.rollback()
