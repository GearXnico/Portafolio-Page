"""Punto de entrada de la API."""

from fastapi import FastAPI
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import settings
from app.middleware import BodySizeLimitMiddleware
from app.routers import admin, bootstrap, contact, health

# Los JSON de la API son chicos: el más grande es un mensaje de contacto (~20 KB).
# La subida de capturas (tarea 2.5) tendrá su propio límite.
MAX_BODY_BYTES = 64 * 1024

app = FastAPI(title="API")
app.include_router(health.router)
app.include_router(bootstrap.router)
app.include_router(contact.router)
app.include_router(admin.public_router)
app.include_router(admin.router)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_BODY_BYTES)
# Va por fuera (se agrega al final) para que todo lo demás vea la IP real del visitante.
if settings.trusted_proxies:
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.trusted_proxies)
