"""Public contact form."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.contact import ContactIn, ContactOut
from app.services import contact
from app.services.rate_limit import SlidingWindowLimiter, client_key

router = APIRouter(prefix="/api", tags=["contact"])

# 5 messages per hour per IP (architecture, section 6).
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
    """Save the message and send the email notice after responding.

    Responds 429 with `Retry-After` over the limit, and 422 if a field is invalid.
    """
    retry_after = limiter.hit(client_key(request))
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many messages. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    # Honeypot filled in: a bot. Respond as if all went well so it gets no clues.
    if payload.website:
        return ContactOut()

    message_id = contact.save_message(session, payload)
    background_tasks.add_task(contact.notify_new_message, message_id)
    return ContactOut()
