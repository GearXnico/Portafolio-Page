"""Page visits and the UTM parameters of the link that brought them.

The IP is not stored: only a hash of the IP, user agent and a salt that changes every day,
enough to count unique visitors per day.
"""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Visit(Base):
    __tablename__ = "visit"
    __table_args__ = (
        CheckConstraint("lang IN ('es', 'en')", name="lang"),
        CheckConstraint("visitor_hash ~ '^[0-9a-f]{64}$'", name="visitor_hash"),
        # UTM and referrer come from the visitor's URL and headers: their length is limited.
        CheckConstraint(
            "char_length(utm_source) <= 200 AND char_length(utm_medium) <= 200"
            " AND char_length(utm_campaign) <= 200 AND char_length(utm_content) <= 200",
            name="utm_length",
        ),
        CheckConstraint("char_length(referrer) <= 2048", name="referrer_length"),
        CheckConstraint("country ~ '^[A-Z]{2}$'", name="country"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Index for the panel's reports, which filter by date.
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    utm_source: Mapped[str | None]
    utm_medium: Mapped[str | None]
    utm_campaign: Mapped[str | None]
    utm_content: Mapped[str | None]
    country: Mapped[str | None]
    lang: Mapped[str]
    referrer: Mapped[str | None]
    visitor_hash: Mapped[str]
