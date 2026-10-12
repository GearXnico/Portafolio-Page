"""Proyectos del portafolio y sus capturas."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Project(Base):
    __tablename__ = "project"
    __table_args__ = (
        # El slug va en la URL: minúsculas, números y guiones simples.
        CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="slug_format"),
        CheckConstraint("position >= 0", name="position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(unique=True)
    title_es: Mapped[str]
    title_en: Mapped[str]
    summary_es: Mapped[str]
    summary_en: Mapped[str]
    # Cuerpo en Markdown.
    body_es: Mapped[str] = mapped_column(server_default="")
    body_en: Mapped[str] = mapped_column(server_default="")
    stack: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'"))
    demo_url: Mapped[str | None]
    repo_url: Mapped[str | None]
    # Un proyecto nuevo queda oculto hasta que se publica desde el panel.
    visible: Mapped[bool] = mapped_column(server_default=text("false"))
    position: Mapped[int] = mapped_column(server_default="0")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    images: Mapped[list[ProjectImage]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProjectImage.position",
    )


class ProjectImage(Base):
    __tablename__ = "project_image"
    __table_args__ = (CheckConstraint("position >= 0", name="position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    # Ruta relativa a /media.
    path: Mapped[str]
    alt_es: Mapped[str] = mapped_column(server_default="")
    alt_en: Mapped[str] = mapped_column(server_default="")
    position: Mapped[int] = mapped_column(server_default="0")

    project: Mapped[Project] = relationship(back_populates="images")
