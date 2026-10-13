"""Visitas para el panel: solo conteos agrupados, nunca filas sueltas ni el hash del visitante."""

from pydantic import BaseModel


class VisitCountOut(BaseModel):
    utm_source: str | None
    utm_campaign: str | None
    visits: int
    # Visitantes únicos por día, sumados: el hash cambia cada día con la sal.
    unique_visitors: int
