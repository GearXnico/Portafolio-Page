"""Contact form messages. They are saved even if the email notice fails."""

from datetime import datetime

from sqlalchemy import CheckConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ContactMessage(Base):
    __tablename__ = "contact_message"
    # Messages come from a public form: the length limits stop abuse even if the API's
    # validation fails. The same values apply to the API (task 2.6).
    __table_args__ = (
        CheckConstraint("lang IN ('es', 'en')", name="lang"),
        CheckConstraint("char_length(name) BETWEEN 1 AND 200", name="name_length"),
        CheckConstraint(r"char_length(email) <= 320 AND email ~ '^[^@\s]+@[^@\s]+$'", name="email"),
        CheckConstraint("char_length(message) BETWEEN 1 AND 5000", name="message_length"),
        CheckConstraint(
            "char_length(utm_source) <= 200 AND char_length(utm_campaign) <= 200",
            name="utm_length",
        ),
    )

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
