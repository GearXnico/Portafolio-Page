"""Rate limit, with a clock controlled by the test."""

import logging

import pytest
from starlette.requests import Request

from app.services.rate_limit import SlidingWindowLimiter, client_key


class Reloj:
    def __init__(self) -> None:
        self.ahora = 1000.0

    def __call__(self) -> float:
        return self.ahora


def test_allows_up_to_the_limit_and_allows_again_after_the_window() -> None:
    reloj = Reloj()
    limite = SlidingWindowLimiter(limit=2, window_seconds=60, clock=reloj)

    assert limite.hit("a") is None
    reloj.ahora += 10
    assert limite.hit("a") is None
    assert limite.hit("a") == 50
    assert limite.hit("b") is None

    reloj.ahora += 50
    assert limite.hit("a") is None
    assert limite.hit("a") == 10


def test_a_rejected_attempt_does_not_extend_the_block() -> None:
    reloj = Reloj()
    limite = SlidingWindowLimiter(limit=1, window_seconds=60, clock=reloj)
    limite.hit("a")

    for _ in range(100):
        limite.hit("a")
    reloj.ahora += 60

    assert limite.hit("a") is None


def test_keeps_no_more_keys_than_the_cap_and_warns_when_dropping_a_current_one(
    caplog: pytest.LogCaptureFixture,
) -> None:
    reloj = Reloj()
    limite = SlidingWindowLimiter(limit=1, window_seconds=60, max_keys=3, clock=reloj)

    with caplog.at_level(logging.WARNING):
        for ip in ["a", "b", "c", "d"]:
            assert limite.hit(ip) is None

    assert "dropped a key with current events" in caplog.text

    assert len(limite._hits) == 3
    # The least recently used key was dropped.
    assert "a" not in limite._hits
    assert limite.hit("d") is not None


def test_when_full_drops_expired_keys_first(caplog: pytest.LogCaptureFixture) -> None:
    reloj = Reloj()
    limite = SlidingWindowLimiter(limit=1, window_seconds=60, max_keys=2, clock=reloj)
    limite.hit("vieja")
    reloj.ahora += 30
    limite.hit("activa")
    reloj.ahora += 40

    limite.hit("nueva")

    assert set(limite._hits) == {"activa", "nueva"}
    assert caplog.text == ""


def pedido(host: str | None) -> Request:
    return Request({"type": "http", "client": (host, 1234) if host else None, "headers": []})


@pytest.mark.parametrize(
    ("host", "clave"),
    [
        ("203.0.113.7", "203.0.113.7"),
        ("2001:db8:1:2:aaaa::1", "2001:db8:1:2::/64"),
        ("2001:db8:1:2:bbbb::9", "2001:db8:1:2::/64"),
        ("::ffff:203.0.113.7", "203.0.113.7"),
        ("testclient", "testclient"),
        (None, "unknown"),
    ],
)
def test_client_key(host: str | None, clave: str) -> None:
    assert client_key(pedido(host)) == clave
