"""Base declarativa y convención de nombres para las restricciones."""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, Text
from sqlalchemy.orm import DeclarativeBase

# Nombres fijos para índices y restricciones: así Alembic genera migraciones estables
# y los tests pueden reconocer qué restricción falló.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Textos como `text` de Postgres (sin largo fijo) y fechas con zona horaria (timestamptz).
    type_annotation_map = {str: Text(), datetime: DateTime(timezone=True)}
