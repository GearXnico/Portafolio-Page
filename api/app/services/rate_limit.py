"""Rate limit per IP (Internet Protocol address), in memory.

It lives in the API process: it resets with each deployment and isn't shared between processes.
That is enough for a site with a single Uvicorn process; if there are ever several, it has to
move to the database or to Redis.
"""

import ipaddress
import logging
import math
import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable

from fastapi import Request

logger = logging.getLogger(__name__)


class SlidingWindowLimiter:
    """Allow `limit` events per key within a sliding window of `window_seconds`."""

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        max_keys: int = 10_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        # Cap on keys in memory, so many different IPs don't fill it.
        self.max_keys = max_keys
        self._clock = clock
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def hit(self, key: str) -> int | None:
        """Record an event. Return None if allowed, or the remaining seconds if not."""
        now = self._clock()
        with self._lock:
            hits = self._hits.get(key)
            if hits is None:
                self._make_room(now)
                hits = self._hits[key] = deque()
            self._hits.move_to_end(key)
            while hits and hits[0] <= now - self.window_seconds:
                hits.popleft()
            if len(hits) >= self.limit:
                return max(1, math.ceil(hits[0] + self.window_seconds - now))
            hits.append(now)
            return None

    def forget(self, key: str) -> None:
        """Delete a key's events, for example after a successful login."""
        with self._lock:
            self._hits.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def _make_room(self, now: float) -> None:
        if len(self._hits) < self.max_keys:
            return
        # First drop the keys with no current events; if that's not enough, the oldest one.
        expired = [k for k, h in self._hits.items() if not h or h[-1] <= now - self.window_seconds]
        for key in expired:
            del self._hits[key]
        while len(self._hits) >= self.max_keys:
            # A dropped key with current events gets its attempts back: this only happens if
            # more distinct IPs than the cap arrive within one window, and it's worth knowing.
            self._hits.popitem(last=False)
            logger.warning("Rate limit full: dropped a key with current events")


def client_key(request: Request) -> str:
    """The visitor's IP as the limit key.

    An IPv6 address is grouped by its /64 network, because any home connection has millions of
    addresses in that range. Behind Caddy, the real IP arrives through X-Forwarded-For only if
    `TRUSTED_PROXIES` includes Caddy (see app/main.py).
    """
    host = request.client.host if request.client else "unknown"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return host
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped:
            return str(ip.ipv4_mapped)
        return str(ipaddress.ip_network(f"{ip}/64", strict=False))
    return str(ip)
