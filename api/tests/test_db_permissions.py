"""The API connects with a minimal-permission user: it can touch rows, not the schema.

If these tests fail, DATABASE_URL probably points to the owner of the tables
instead of the API user (see docs/api.md, "Database: two users").
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db import engine


def ejecutar(sql: str) -> None:
    with engine.connect() as connection:
        connection.execute(text(sql))
        connection.rollback()


def test_api_user_is_neither_superuser_nor_owner() -> None:
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
def test_api_user_cannot_change_the_schema(sql: str) -> None:
    with pytest.raises(ProgrammingError, match="InsufficientPrivilege|permission denied|must be"):
        ejecutar(sql)


def test_api_user_reads_and_writes_rows() -> None:
    with engine.connect() as connection:
        connection.execute(text("INSERT INTO skill (name, category) VALUES ('Python', 'language')"))
        connection.execute(text("UPDATE skill SET position = 1"))
        assert connection.execute(text("SELECT count(*) FROM skill")).scalar_one() >= 1
        connection.execute(text("DELETE FROM skill"))
        connection.rollback()
