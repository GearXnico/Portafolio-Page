"""Visitas a la página, con su origen (UTM, parámetros de origen del enlace).

No se guarda la IP: solo un hash de IP, user agent y una sal que cambia cada día,
suficiente para contar visitantes únicos por día.
"""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Visit(Base):
    __tablename__ = "visit"
    __table_args__ = (
        CheckConstraint("lang IN ('es', 'en')", name="lang"),
        # sha256 en hexadecimal.
        CheckConstraint("visitor_hash ~ '^[0-9a-f]{64}$'", name="visitor_hash"),
        # UTM y referrer vienen de la URL y de los headers del visitante: se limita su largo.
        CheckConstraint(
            "char_length(utm_source) <= 200 AND char_length(utm_medium) <= 200"
            " AND char_length(utm_campaign) <= 200 AND char_length(utm_content) <= 200",
            name="utm_length",
        ),
        CheckConstraint("char_length(referrer) <= 2048", name="referrer_length"),
        # Código de país ISO 3166-1 de dos letras.
        CheckConstraint("country ~ '^[A-Z]{2}$'", name="country"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Índice para los reportes del panel, que filtran por fecha.
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    utm_source: Mapped[str | None]
    utm_medium: Mapped[str | None]
    utm_campaign: Mapped[str | None]
    utm_content: Mapped[str | None]
    country: Mapped[str | None]
    lang: Mapped[str]
    referrer: Mapped[str | None]
    visitor_hash: Mapped[str]
