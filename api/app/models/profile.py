"""Perfil del dueño del sitio. Hay una sola fila (id = 1)."""

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import URL_HTTPS_REGEX, Base


class Profile(Base):
    __tablename__ = "profile"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_row"),
        # Un objeto cuyos valores son todos enlaces https (ver URL_HTTPS_REGEX).
        CheckConstraint(
            "jsonb_typeof(links) = 'object' AND NOT jsonb_path_exists(links, "
            f'\'strict $.* ? (@.type() != "string" || !(@ like_regex "{URL_HTTPS_REGEX}"))\')',
            name="links_https",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False, default=1)
    headline_es: Mapped[str]
    headline_en: Mapped[str]
    about_es: Mapped[str]
    about_en: Mapped[str]
    contact_email: Mapped[str]
    # Enlaces externos, por ejemplo {"github": "...", "linkedin": "...", "cv": "..."}.
    links: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
