"""Experiencia laboral. `end_date` vacío significa el trabajo actual."""

from datetime import date

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Experience(Base):
    __tablename__ = "experience"
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="dates"),
        CheckConstraint("position >= 0", name="position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str]
    role_es: Mapped[str]
    role_en: Mapped[str]
    description_es: Mapped[str] = mapped_column(server_default="")
    description_en: Mapped[str] = mapped_column(server_default="")
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    position: Mapped[int] = mapped_column(server_default="0")
