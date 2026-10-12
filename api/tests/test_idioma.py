import pytest

from app.idioma import decidir_idioma, es_idioma, idioma_preferido


@pytest.mark.parametrize(
    ("accept_language", "esperado"),
    [
        ("es", "es"),
        ("es-CL,es;q=0.9,en;q=0.8", "es"),
        ("ES-cl", "es"),
        ("en-US,en;q=0.9,es;q=0.8", "en"),
        ("en", "en"),
        ("fr-FR,fr;q=0.9", "en"),
        # Manda la calidad (q), no el orden.
        ("en;q=0.5,es", "es"),
        # Con la misma calidad, gana el primero.
        ("es;q=0.8,en;q=0.8", "es"),
        # q=0 significa "no lo quiero".
        ("es;q=0,en", "en"),
        ("*", "en"),
        ("es;q=abc,en", "en"),
        ("es;q=2,en", "en"),
        ("", "en"),
        (None, "en"),
        (",,;;", "en"),
        # Un header absurdamente largo se ignora.
        ("es," + "x" * 600, "en"),
    ],
)
def test_decidir_idioma(accept_language: str | None, esperado: str) -> None:
    assert decidir_idioma(accept_language) == esperado


def test_el_pais_todavia_no_cambia_el_idioma() -> None:
    assert decidir_idioma("en-US", pais="CL") == "en"


def test_idioma_preferido_devuelve_el_idioma_principal() -> None:
    assert idioma_preferido("pt-BR,pt;q=0.9") == "pt"


@pytest.mark.parametrize(
    ("valor", "esperado"), [("es", "es"), ("en", "en"), ("fr", None), ("ES", None), (None, None)]
)
def test_es_idioma(valor: str | None, esperado: str | None) -> None:
    assert es_idioma(valor) == esperado
