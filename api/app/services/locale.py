"""The only place that decides the page language."""

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

    Browsers put the preferred language first (`es-CL,es;q=0.9,en;q=0.8`). `country` is
    accepted so detection by country can be added here without touching the callers.
    """
    del country
    first = (accept_language or "").split(",", 1)[0].split(";", 1)[0]
    return "es" if first.strip().lower().split("-", 1)[0] == "es" else "en"
