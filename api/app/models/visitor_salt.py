"""Sal diaria para el hash de visitantes.

Se genera al azar la primera vez que alguien visita el sitio cada día (UTC) y se borra
al día siguiente. Sin la sal, los hashes de días anteriores no se pueden recalcular,
ni siquiera con un respaldo de la base: no hay forma de volver a la IP.
"""

from datetime import date

from sqlalchemy import CheckConstraint, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

SALT_BYTES = 32


class VisitorSalt(Base):
    __tablename__ = "visitor_salt"
    __table_args__ = (CheckConstraint(f"octet_length(salt) = {SALT_BYTES}", name="salt_length"),)

    day: Mapped[date] = mapped_column(primary_key=True)
    salt: Mapped[bytes] = mapped_column(LargeBinary)
