from alembic import command
from alembic.config import Config


def test_las_migraciones_se_aplican_y_revierten() -> None:
    config = Config("alembic.ini")

    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
