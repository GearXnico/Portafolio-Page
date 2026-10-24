"""Portfolio projects and their screenshots."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import URL_HTTPS_REGEX, URL_MAX_LENGTH, Base


class Project(Base):
    __tablename__ = "project"
    __table_args__ = (
        # The slug goes in the URL: lowercase letters, digits and single hyphens.
        CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="slug_format"),
        CheckConstraint("position >= 0", name="position"),
        CheckConstraint(
            f"char_length(demo_url) <= {URL_MAX_LENGTH} AND demo_url ~ '{URL_HTTPS_REGEX}'",
            name="demo_url",
        ),
        CheckConstraint(
            f"char_length(repo_url) <= {URL_MAX_LENGTH} AND repo_url ~ '{URL_HTTPS_REGEX}'",
            name="repo_url",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(unique=True)
    title_es: Mapped[str]
    title_en: Mapped[str]
    summary_es: Mapped[str]
    summary_en: Mapped[str]
    body_es: Mapped[str] = mapped_column(server_default="")
    body_en: Mapped[str] = mapped_column(server_default="")
    stack: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'"))
    demo_url: Mapped[str | None]
    repo_url: Mapped[str | None]
    # A new project stays hidden until it is published from the panel.
    visible: Mapped[bool] = mapped_column(server_default=text("false"))
    position: Mapped[int] = mapped_column(server_default="0")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    images: Mapped[list[ProjectImage]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProjectImage.position",
        # The panel and the page always show the screenshots with their project.
        lazy="selectin",
    )


class ProjectImage(Base):
    __tablename__ = "project_image"
    __table_args__ = (
        CheckConstraint("position >= 0", name="position"),
        # Relative path inside /media: no "..", no leading "/" and no backslashes.
        CheckConstraint(
            r"path ~ '^[A-Za-z0-9_-][A-Za-z0-9_./-]*$' AND path !~ '\.\.'", name="path"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    path: Mapped[str]
    alt_es: Mapped[str] = mapped_column(server_default="")
    alt_en: Mapped[str] = mapped_column(server_default="")
    position: Mapped[int] = mapped_column(server_default="0")

    project: Mapped[Project] = relationship(back_populates="images")

    @property
    def url(self) -> str:
        """Public address of the screenshot, served by Caddy."""
        return f"/media/{self.path}"
