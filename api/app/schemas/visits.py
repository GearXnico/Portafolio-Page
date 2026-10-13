"""Visits for the panel: only grouped counts, never individual rows or the visitor hash."""

from pydantic import BaseModel


class VisitCountOut(BaseModel):
    utm_source: str | None
    utm_campaign: str | None
    visits: int
    # Unique visitors per day, summed: the hash changes every day with the salt.
    unique_visitors: int
