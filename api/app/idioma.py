"""Decide el idioma de la página (ADR 0002).

Todo pasa por `decidir_idioma`, para que el día que se use el país (Cloudflare,
header `CF-IPCountry`) baste con cambiar esta función.
"""

from typing import Literal, get_args

Idioma = Literal["es", "en"]
IDIOMAS: tuple[Idioma, ...] = get_args(Idioma)
IDIOMA_POR_DEFECTO: Idioma = "en"

# Un Accept-Language real tiene unas pocas decenas de caracteres. Más que esto se ignora,
# para no gastar CPU (procesador) en un header armado para abusar.
_ACCEPT_LANGUAGE_MAX = 500


def es_idioma(valor: str | None) -> Idioma | None:
    """Devuelve el idioma si `valor` es uno de los soportados; si no, None."""
    for idioma in IDIOMAS:
        if valor == idioma:
            return idioma
    return None


def _calidad(parametros: list[str]) -> float:
    """Lee el `q=` de una entrada de Accept-Language (1 si no viene o no se entiende)."""
    for parametro in parametros:
        nombre, _, valor = parametro.partition("=")
        if nombre.strip().lower() == "q":
            try:
                calidad = float(valor)
            except ValueError:
                return 0.0
            return calidad if 0.0 <= calidad <= 1.0 else 0.0
    return 1.0


def idioma_preferido(accept_language: str | None) -> str | None:
    """El idioma principal (por ejemplo "es" de "es-CL") con mayor prioridad, o None."""
    if not accept_language or len(accept_language) > _ACCEPT_LANGUAGE_MAX:
        return None
    candidatos: list[tuple[float, str]] = []
    for entrada in accept_language.split(","):
        etiqueta, *parametros = entrada.split(";")
        etiqueta = etiqueta.strip().lower()
        calidad = _calidad(parametros)
        if etiqueta and etiqueta != "*" and calidad > 0:
            candidatos.append((calidad, etiqueta.split("-")[0]))
    if not candidatos:
        return None
    # sorted es estable: con la misma calidad gana el que viene primero en la lista.
    return sorted(candidatos, key=lambda candidato: -candidato[0])[0][1]


def decidir_idioma(accept_language: str | None, pais: str | None = None) -> Idioma:
    """Español si el idioma preferido del navegador es español; si no, inglés.

    `pais` queda reservado para la detección por país (código ISO 3166-1, como "CL");
    en la versión 1 no se usa.
    """
    del pais  # Reservado para cuando el país venga de Cloudflare.
    return "es" if idioma_preferido(accept_language) == "es" else IDIOMA_POR_DEFECTO
