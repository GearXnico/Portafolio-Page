"""Declarative base and naming convention for constraints."""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, Text
from sqlalchemy.orm import DeclarativeBase

# Fixed names for indexes and constraints: this way Alembic generates stable migrations
# and tests can tell which constraint failed.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Links the page shows in an <a href>: https only, with a host and no spaces, so that a
# `javascript:` link never reaches the page. POSIX classes avoid "\\" escapes.
URL_HTTPS_REGEX = "^https://[^[:space:]/]+[^[:space:]]*$"
URL_MAX_LENGTH = 2048


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Strings as Postgres `text` (no fixed length) and datetimes with time zone (timestamptz).
    type_annotation_map = {str: Text(), datetime: DateTime(timezone=True)}
