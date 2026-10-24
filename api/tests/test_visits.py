from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import VisitorSalt
from app.services.visits import clean_text, daily_salt, referrer_origin, visitor_hash


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("linkedin", "linkedin"),
        ("  linkedin  ", "linkedin"),
        ("", None),
        ("   ", None),
        (None, None),
        # Null byte, line breaks and tabs.
        ("link\x00ed\nin\t", "linkedin"),
        # Invisible and text-direction characters (U+202E reverses what follows).
        ("‮nideknil​", "nideknil"),
        # Unicode line and paragraph separators.
        ("linked\u2028in\u2029", "linkedin"),
        ("correo de otoño", "correo de otoño"),
    ],
)
def test_clean_text(value: str | None, expected: str | None) -> None:
    assert clean_text(value, 200) == expected


def test_clean_text_trims_to_the_maximum_length() -> None:
    assert clean_text("a" * 500, 200) == "a" * 200


def test_clean_text_does_not_walk_a_huge_value() -> None:
    # Only the start is looked at: whatever comes after the margin doesn't reach the result.
    assert clean_text("\x00" * 10 + "a" * 10 + "b" * 100_000, 5) == "aaaaa"


@pytest.mark.parametrize(
    ("referrer", "expected"),
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
def test_referrer_origin(referrer: str | None, expected: str | None) -> None:
    assert referrer_origin(referrer) == expected


def test_hash_is_stable_within_the_day_and_does_not_contain_the_ip() -> None:
    salt = b"s" * 32
    hash_1 = visitor_hash(salt, "203.0.113.7", "Firefox")

    assert hash_1 == visitor_hash(salt, "203.0.113.7", "Firefox")
    assert len(hash_1) == 64
    assert "203.0.113.7" not in hash_1
    assert hash_1 != visitor_hash(salt, "203.0.113.8", "Firefox")
    assert hash_1 != visitor_hash(salt, "203.0.113.7", "Chrome")
    assert hash_1 != visitor_hash(b"t" * 32, "203.0.113.7", "Firefox")


def test_salt_is_created_once_per_day(db_session: Session) -> None:
    day = date(2030, 1, 15)

    salt = daily_salt(db_session, day)

    assert len(salt) == 32
    assert daily_salt(db_session, day) == salt


def test_a_new_day_brings_a_new_salt_and_deletes_the_old_one(db_session: Session) -> None:
    yesterday_salt = daily_salt(db_session, date(2030, 1, 15))

    today_salt = daily_salt(db_session, date(2030, 1, 16))

    assert today_salt != yesterday_salt
    days = db_session.scalars(select(VisitorSalt.day)).all()
    assert days == [date(2030, 1, 16)]
    assert db_session.scalar(select(func.count()).select_from(VisitorSalt)) == 1
