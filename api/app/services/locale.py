"""Decide el idioma de la página (ADR 0002).

Todo pasa por `decide_locale`, para que el día que se use el país (Cloudflare,
header `CF-IPCountry`) baste con cambiar esta función.
"""

from typing import Literal

Lang = Literal["es", "en"]


def parse_lang(value: str | None) -> Lang | None:
    """Devuelve el idioma si `value` es uno de los soportados; si no, None."""
    if value == "es":
        return "es"
    if value == "en":
        return "en"
    return None


def decide_locale(country: str | None, accept_language: str | None) -> Lang:
    """Español si el primer idioma del navegador es español; si no, inglés.

    Los navegadores ponen primero el idioma preferido (`es-CL,es;q=0.9,en;q=0.8`), así que
    basta con mirar la primera entrada. `country` queda reservado para la detección por país
    (código ISO 3166-1, como "CL"); en la versión 1 no se usa.
    """
    del country  # Reservado para cuando el país venga de Cloudflare.
    first = (accept_language or "").split(",", 1)[0].split(";", 1)[0]
    return "es" if first.strip().lower().split("-", 1)[0] == "es" else "en"
