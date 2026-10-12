"""Punto de entrada de la API."""

import re

from fastapi import FastAPI, Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import settings
from app.middleware import BodySizeLimitMiddleware
from app.routers import admin, admin_content, bootstrap, contact, health
from app.services.images import MAX_IMAGE_BYTES

# Los JSON de la API son chicos: el más grande es un proyecto con sus dos cuerpos en Markdown
# (hasta 10.000 caracteres cada uno, ~25 KB en español).
MAX_BODY_BYTES = 64 * 1024
# La subida de capturas: la imagen (5 MB) más los textos alternativos y los separadores del
# formulario. El tamaño exacto de la imagen lo revisa app/services/images.py.
UPLOAD_PATHS = re.compile(r"/api/admin/projects/\d+/images")
MAX_UPLOAD_BYTES = MAX_IMAGE_BYTES + 64 * 1024


def _is_admin(request: Request) -> bool:
    return admin.has_session(request.cookies.get(admin.COOKIE_NAME))


app = FastAPI(title="API")
app.include_router(health.router)
app.include_router(bootstrap.router)
app.include_router(contact.router)
app.include_router(admin.public_router)
app.include_router(admin.router)
app.include_router(admin_content.router)
app.add_middleware(
    BodySizeLimitMiddleware,
    max_bytes=MAX_BODY_BYTES,
    upload_paths=UPLOAD_PATHS,
    upload_max_bytes=MAX_UPLOAD_BYTES,
    upload_allowed=_is_admin,
)
# Va por fuera (se agrega al final) para que todo lo demás vea la IP real del visitante.
if settings.trusted_proxies:
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.trusted_proxies)
