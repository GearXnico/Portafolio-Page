"""Modelos de SQLAlchemy. Alembic usa `Base.metadata` para autogenerar migraciones."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
