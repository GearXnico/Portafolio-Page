"""Middlewares ASGI (interfaz entre el servidor y la app) propios de la API."""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}


class BodySizeLimitMiddleware:
    """Rechaza cuerpos más grandes que `max_bytes` antes de leerlos.

    Exige `Content-Length`, que los navegadores siempre mandan con `fetch`: sin él, un cuerpo
    por partes (chunked) no se puede medir de antemano. Caddy pone otro límite delante.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] in METHODS_WITH_BODY:
            headers = dict(scope["headers"])
            length = headers.get(b"content-length")
            if length is None or not length.isdigit():
                response = JSONResponse({"detail": "Falta Content-Length"}, status_code=411)
                return await response(scope, receive, send)
            if int(length) > self.max_bytes:
                response = JSONResponse({"detail": "El cuerpo es demasiado grande"}, 413)
                return await response(scope, receive, send)
        await self.app(scope, receive, send)
