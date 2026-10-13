"""Daily salt for the visitor hash.

It is generated at random the first time someone visits the site each day (UTC) and deleted
the next day. Without the salt, hashes from earlier days can't be recomputed, not even
with a database backup: there is no way back to the IP.
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
