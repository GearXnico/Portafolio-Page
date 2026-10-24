import re

from fastapi import FastAPI, Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import settings
from app.middleware import BodySizeLimitMiddleware
from app.routers import admin, admin_activity, admin_content, bootstrap, contact, health
from app.services.images import MAX_IMAGE_BYTES

# The API's JSON bodies are small: the largest is a project with its two Markdown bodies
# (up to 10,000 characters each, ~25 KB in Spanish).
MAX_BODY_BYTES = 64 * 1024
# The image plus the alt texts and form separators; images.py checks the exact image size.
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
app.include_router(admin_activity.router)
app.add_middleware(
    BodySizeLimitMiddleware,
    max_bytes=MAX_BODY_BYTES,
    upload_paths=UPLOAD_PATHS,
    upload_max_bytes=MAX_UPLOAD_BYTES,
    upload_allowed=_is_admin,
)
# Goes outermost (added last) so everything else sees the visitor's real IP.
if settings.trusted_proxies:
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.trusted_proxies)
