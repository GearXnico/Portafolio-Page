import pytest

from app.idioma import decidir_idioma, es_idioma


@pytest.mark.parametrize(
    ("accept_language", "esperado"),
    [
        ("es", "es"),
        ("es-CL,es;q=0.9,en;q=0.8", "es"),
        ("ES-cl", "es"),
        ("es;q=0.9", "es"),
        ("en-US,en;q=0.9,es;q=0.8", "en"),
        ("en", "en"),
        ("fr-FR,fr;q=0.9", "en"),
        ("estonio", "en"),
        ("*", "en"),
        ("", "en"),
        (None, "en"),
        (",,;;", "en"),
    ],
)
def test_decidir_idioma(accept_language: str | None, esperado: str) -> None:
    assert decidir_idioma(accept_language) == esperado


def test_el_pais_todavia_no_cambia_el_idioma() -> None:
    assert decidir_idioma("en-US", pais="CL") == "en"


@pytest.mark.parametrize(
    ("valor", "esperado"), [("es", "es"), ("en", "en"), ("fr", None), ("ES", None), (None, None)]
)
def test_es_idioma(valor: str | None, esperado: str | None) -> None:
    assert es_idioma(valor) == esperado
