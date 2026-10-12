"""Decide el idioma de la página (ADR 0002).

Todo pasa por `decidir_idioma`, para que el día que se use el país (Cloudflare,
header `CF-IPCountry`) baste con cambiar esta función.
"""

from typing import Literal

Idioma = Literal["es", "en"]


def es_idioma(valor: str | None) -> Idioma | None:
    """Devuelve el idioma si `valor` es uno de los soportados; si no, None."""
    if valor == "es":
        return "es"
    if valor == "en":
        return "en"
    return None


def decidir_idioma(accept_language: str | None, pais: str | None = None) -> Idioma:
    """Español si el primer idioma del navegador es español; si no, inglés.

    Los navegadores ponen primero el idioma preferido (`es-CL,es;q=0.9,en;q=0.8`), así que
    basta con mirar la primera entrada. `pais` queda reservado para la detección por país
    (código ISO 3166-1, como "CL"); en la versión 1 no se usa.
    """
    del pais  # Reservado para cuando el país venga de Cloudflare.
    primero = (accept_language or "").split(",", 1)[0].split(";", 1)[0]
    return "es" if primero.strip().lower().split("-", 1)[0] == "es" else "en"
