"""Technical skills shown on the page, grouped by category."""

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Values stored in the database; the frontend translates them into each language.
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
