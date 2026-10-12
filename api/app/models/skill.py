"""Habilidades técnicas que muestra la página, agrupadas por categoría."""

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Valores guardados en la base; el frontend los traduce a cada idioma.
SKILL_CATEGORIES = ("language", "framework", "tool")


class Skill(Base):
    __tablename__ = "skill"
    __table_args__ = (
        CheckConstraint(
            "category IN ({})".format(", ".join(f"'{c}'" for c in SKILL_CATEGORIES)),
            name="category",
        ),
        CheckConstraint("position >= 0", name="position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    category: Mapped[str]
    position: Mapped[int] = mapped_column(server_default="0")
