"""Decide the page language (ADR (Architecture Decision Record) 0002).

Everything goes through `decide_locale`, so that the day the country is used (Cloudflare,
`CF-IPCountry` header) changing this function is enough.
"""

from typing import Literal

Lang = Literal["es", "en"]


def parse_lang(value: str | None) -> Lang | None:
    """Return the language if `value` is a supported one; otherwise, None."""
    if value == "es":
        return "es"
    if value == "en":
        return "en"
    return None


def decide_locale(country: str | None, accept_language: str | None) -> Lang:
    """Spanish if the browser's first language is Spanish; otherwise, English.

    Browsers put the preferred language first (`es-CL,es;q=0.9,en;q=0.8`), so looking at the
    first entry is enough. `country` is reserved for detection by country (ISO 3166-1 code,
    like "CL"); version 1 doesn't use it.
    """
    del country  # Reserved for when the country comes from Cloudflare.
    first = (accept_language or "").split(",", 1)[0].split(";", 1)[0]
    return "es" if first.strip().lower().split("-", 1)[0] == "es" else "en"
