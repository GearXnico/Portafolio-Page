"""Formulario de contacto público."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.contact import ContactIn, ContactOut
from app.services import contact
from app.services.rate_limit import SlidingWindowLimiter, client_key

router = APIRouter(prefix="/api", tags=["contact"])

# 5 mensajes por hora por IP (arquitectura, sección 6).
contact_limiter = SlidingWindowLimiter(limit=5, window_seconds=60 * 60)


def get_contact_limiter() -> SlidingWindowLimiter:
    return contact_limiter


@router.post("/contact", status_code=status.HTTP_201_CREATED)
def create_contact_message(
    payload: ContactIn,
    request: Request,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
    limiter: Annotated[SlidingWindowLimiter, Depends(get_contact_limiter)],
) -> ContactOut:
    """Guarda el mensaje y avisa por correo después de responder.

    Responde 429 con `Retry-After` al pasar el límite, y 422 si un campo no es válido.
    """
    retry_after = limiter.hit(client_key(request))
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados mensajes. Intenta más tarde.",
            headers={"Retry-After": str(retry_after)},
        )
    # Honeypot lleno: un bot. Se responde como si todo saliera bien para no darle pistas.
    if payload.website:
        return ContactOut()

    message_id = contact.save_message(session, payload)
    background_tasks.add_task(contact.notify_new_message, message_id)
    return ContactOut()
