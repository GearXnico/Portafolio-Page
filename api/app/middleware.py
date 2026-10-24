import re
from collections.abc import Callable

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}


class BodySizeLimitMiddleware:
    """Reject bodies larger than `max_bytes` before reading them.

    Routes matching `upload_paths` (the screenshot upload) have their own limit,
    `upload_max_bytes`, and only whoever passes `upload_allowed` (the administrator) gets it:
    FastAPI reads the form before checking the session, so without this an anonymous user could
    send 5 MB per request. Requires `Content-Length`, which browsers always send with `fetch`:
    without it, a chunked body can't be measured in advance. Caddy puts another limit in front.
    """

    def __init__(
        self,
        app: ASGIApp,
        max_bytes: int,
        upload_paths: re.Pattern[str] | None = None,
        upload_max_bytes: int = 0,
        upload_allowed: Callable[[Request], bool] = lambda request: False,
    ) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.upload_paths = upload_paths
        self.upload_max_bytes = upload_max_bytes
        self.upload_allowed = upload_allowed

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] in METHODS_WITH_BODY:
            headers = dict(scope["headers"])
            length = headers.get(b"content-length")
            if length is None or not length.isdigit():
                response = JSONResponse({"detail": "Content-Length is missing"}, status_code=411)
                return await response(scope, receive, send)
            is_upload = self.upload_paths is not None and self.upload_paths.fullmatch(scope["path"])
            if is_upload and not self.upload_allowed(Request(scope)):
                response = JSONResponse({"detail": "Log in."}, status_code=401)
                return await response(scope, receive, send)
            max_bytes = self.upload_max_bytes if is_upload else self.max_bytes
            if int(length) > max_bytes:
                response = JSONResponse({"detail": "The body is too large"}, 413)
                return await response(scope, receive, send)
        await self.app(scope, receive, send)
