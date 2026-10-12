"""Login, logout y sesión del panel de administración.

Toda ruta `/api/admin/*` va en `router`, que exige sesión por defecto. Solo el login y el
logout van en `public_router`.
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from app.schemas.admin import LoginIn, SessionOut
from app.services import auth
from app.services.rate_limit import SlidingWindowLimiter, client_key

COOKIE_NAME = "admin_session"
COOKIE_PATH = "/api/admin"

# 5 intentos fallidos cada 15 minutos por IP (ADR 0004). Un login correcto borra la cuenta.
login_limiter = SlidingWindowLimiter(limit=5, window_seconds=15 * 60)


def get_login_limiter() -> SlidingWindowLimiter:
    return login_limiter


def require_admin(
    admin_session: Annotated[str | None, Cookie()] = None,
) -> None:
    """Dependencia de toda ruta protegida: 401 si no hay una sesión válida."""
    if not admin_session or not auth.is_valid_session(admin_session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inicia sesión.")


public_router = APIRouter(prefix="/api/admin", tags=["admin"])
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@public_router.post("/login")
def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    limiter: Annotated[SlidingWindowLimiter, Depends(get_login_limiter)],
) -> SessionOut:
    """Deja la cookie de sesión. 401 si las credenciales no calzan; 429 al pasar el límite."""
    if not auth.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El login del administrador no está configurado.",
        )
    key = client_key(request)
    retry_after = limiter.hit(key)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intenta más tarde.",
            headers={"Retry-After": str(retry_after)},
        )
    if not auth.verify_credentials(payload.email, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos."
        )
    limiter.forget(key)
    response.set_cookie(
        COOKIE_NAME,
        auth.create_session_token(),
        max_age=auth.SESSION_DAYS * 24 * 60 * 60,
        path=COOKIE_PATH,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return SessionOut()


@public_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    """Borra la cookie. Responde igual con o sin sesión."""
    response.delete_cookie(
        COOKIE_NAME, path=COOKIE_PATH, secure=True, httponly=True, samesite="strict"
    )


@router.get("/session")
def session() -> SessionOut:
    """200 si hay sesión; el panel lo usa para saber si mostrar el login."""
    return SessionOut()
