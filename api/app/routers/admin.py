"""Login, logout and session of the admin panel.

Every `/api/admin/*` route goes in `router`, which requires a session by default. Only login
and logout go in `public_router`.
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from app.schemas.admin import LoginIn, SessionOut
from app.services import auth
from app.services.rate_limit import SlidingWindowLimiter, client_key

COOKIE_NAME = "admin_session"
COOKIE_PATH = "/api/admin"

# A successful login resets the count.
login_limiter = SlidingWindowLimiter(limit=5, window_seconds=15 * 60)


def get_login_limiter() -> SlidingWindowLimiter:
    return login_limiter


def has_session(admin_session: str | None) -> bool:
    return bool(admin_session) and auth.is_valid_session(admin_session or "")


def require_admin(
    admin_session: Annotated[str | None, Cookie()] = None,
) -> None:
    """Dependency of every protected route: 401 if there is no valid session."""
    if not has_session(admin_session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Log in.")


public_router = APIRouter(prefix="/api/admin", tags=["admin"])
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@public_router.post("/login")
def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    limiter: Annotated[SlidingWindowLimiter, Depends(get_login_limiter)],
) -> SessionOut:
    """Set the session cookie. 401 if the credentials don't match; 429 over the limit."""
    if not auth.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The administrator login is not configured.",
        )
    key = client_key(request)
    retry_after = limiter.hit(key)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    if not auth.verify_credentials(payload.email, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password."
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
    """Delete the cookie. Responds the same with or without a session."""
    response.delete_cookie(
        COOKIE_NAME, path=COOKIE_PATH, secure=True, httponly=True, samesite="strict"
    )


@router.get("/session")
def session() -> SessionOut:
    """200 if there is a session; the panel uses it to know whether to show the login."""
    return SessionOut()
