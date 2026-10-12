from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import VisitorSalt
from app.visitas import hash_visitante, limpiar_texto, origen_del_referrer, sal_del_dia


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("linkedin", "linkedin"),
        ("  linkedin  ", "linkedin"),
        ("", None),
        ("   ", None),
        (None, None),
        # Byte nulo, saltos de línea y tabulaciones.
        ("link\x00ed\nin\t", "linkedin"),
        # Caracteres invisibles y de dirección del texto (U+202E invierte lo que sigue).
        ("‮nideknil​", "nideknil"),
        # Separadores de línea y de párrafo de Unicode.
        ("linked\u2028in\u2029", "linkedin"),
        ("correo de otoño", "correo de otoño"),
    ],
)
def test_limpiar_texto(valor: str | None, esperado: str | None) -> None:
    assert limpiar_texto(valor, 200) == esperado


def test_limpiar_texto_recorta_al_largo_maximo() -> None:
    assert limpiar_texto("a" * 500, 200) == "a" * 200


def test_limpiar_texto_no_recorre_todo_un_valor_enorme() -> None:
    # Solo se mira el comienzo: lo que viene después del margen no entra al resultado.
    assert limpiar_texto("\x00" * 10 + "a" * 10 + "b" * 100_000, 5) == "aaaaa"


@pytest.mark.parametrize(
    ("referrer", "esperado"),
    [
        ("https://www.linkedin.com/feed/?q=nombre%20apellido", "https://www.linkedin.com"),
        ("http://Ejemplo.CL/ruta", "http://ejemplo.cl"),
        ("https://usuario:clave@ejemplo.cl/x", "https://ejemplo.cl"),
        ("https://ejemplo.cl:8443/x", "https://ejemplo.cl:8443"),
        ("javascript:alert(1)", None),
        ("data:text/html,hola", None),
        ("ftp://ejemplo.cl", None),
        ("https://", None),
        ("https://[::1", None),
        ("https://ejemplo.cl:99999/", None),
        ("https://exa mple.cl/", None),
        ("https://ejemplo.cl/" + "a" * 3000, None),
        ("no es una url", None),
        ("", None),
        (None, None),
    ],
)
def test_origen_del_referrer(referrer: str | None, esperado: str | None) -> None:
    assert origen_del_referrer(referrer) == esperado


def test_el_hash_es_estable_en_el_dia_y_no_contiene_la_ip() -> None:
    sal = b"s" * 32
    hash_1 = hash_visitante(sal, "203.0.113.7", "Firefox")

    assert hash_1 == hash_visitante(sal, "203.0.113.7", "Firefox")
    assert len(hash_1) == 64
    assert "203.0.113.7" not in hash_1
    assert hash_1 != hash_visitante(sal, "203.0.113.8", "Firefox")
    assert hash_1 != hash_visitante(sal, "203.0.113.7", "Chrome")
    assert hash_1 != hash_visitante(b"t" * 32, "203.0.113.7", "Firefox")


def test_la_sal_se_crea_una_vez_por_dia(db_session: Session) -> None:
    dia = date(2030, 1, 15)

    sal = sal_del_dia(db_session, dia)

    assert len(sal) == 32
    assert sal_del_dia(db_session, dia) == sal


def test_al_cambiar_el_dia_la_sal_cambia_y_la_anterior_se_borra(db_session: Session) -> None:
    sal_ayer = sal_del_dia(db_session, date(2030, 1, 15))

    sal_hoy = sal_del_dia(db_session, date(2030, 1, 16))

    assert sal_hoy != sal_ayer
    dias = db_session.scalars(select(VisitorSalt.day)).all()
    assert dias == [date(2030, 1, 16)]
    assert db_session.scalar(select(func.count()).select_from(VisitorSalt)) == 1
