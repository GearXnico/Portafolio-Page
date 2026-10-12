"""Límite de frecuencia por IP (dirección de red), en memoria.

Vive en el proceso de la API: se reinicia con cada despliegue y no se comparte entre procesos.
Para un sitio con un solo proceso de Uvicorn alcanza; si algún día hay varios, hay que moverlo
a la base o a Redis.
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
    """Permite `limit` eventos por clave dentro de una ventana móvil de `window_seconds`."""

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        max_keys: int = 10_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        # Tope de claves en memoria, para que muchas IP distintas no la llenen.
        self.max_keys = max_keys
        self._clock = clock
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def hit(self, key: str) -> int | None:
        """Registra un evento. Devuelve None si se permite, o los segundos que faltan si no."""
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
        """Borra los eventos de una clave, por ejemplo tras un login correcto."""
        with self._lock:
            self._hits.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def _make_room(self, now: float) -> None:
        if len(self._hits) < self.max_keys:
            return
        # Primero se botan las claves sin eventos vigentes; si no alcanza, la más antigua.
        expired = [k for k, h in self._hits.items() if not h or h[-1] <= now - self.window_seconds]
        for key in expired:
            del self._hits[key]
        while len(self._hits) >= self.max_keys:
            # Una clave con eventos vigentes que se bota recupera sus intentos: solo pasa si
            # llegan más IP distintas que el tope en una ventana, y conviene enterarse.
            self._hits.popitem(last=False)
            logger.warning("Límite de frecuencia lleno: se botó una clave con eventos vigentes")


def client_key(request: Request) -> str:
    """La IP del visitante como clave del límite.

    Una IPv6 se agrupa por su red /64, porque cualquier conexión doméstica tiene millones de
    direcciones en ese rango. Detrás de Caddy, la IP real llega por X-Forwarded-For solo si
    `TRUSTED_PROXIES` incluye a Caddy (ver app/main.py).
    """
    host = request.client.host if request.client else "desconocido"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return host
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped:
            return str(ip.ipv4_mapped)
        return str(ipaddress.ip_network(f"{ip}/64", strict=False))
    return str(ip)
