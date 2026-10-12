"""Mensajes del formulario de contacto. Se guardan aunque falle el aviso por correo."""

from datetime import datetime

from sqlalchemy import CheckConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ContactMessage(Base):
    __tablename__ = "contact_message"
    __table_args__ = (CheckConstraint("lang IN ('es', 'en')", name="lang"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    name: Mapped[str]
    email: Mapped[str]
    message: Mapped[str]
    lang: Mapped[str]
    utm_source: Mapped[str | None]
    utm_campaign: Mapped[str | None]
    read: Mapped[bool] = mapped_column(server_default=text("false"))
    emailed: Mapped[bool] = mapped_column(server_default=text("false"))
