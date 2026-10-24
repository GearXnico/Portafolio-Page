"""Contact messages and visits by UTM, for the panel.

Every route requires the administrator's session (`require_admin`, on the whole router).
Messages carry the sender's personal data; visits come out only as counts.
"""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import ContactMessage
from app.routers.admin import require_admin
from app.schemas.contact import ContactMessageOut, MessageReadIn
from app.schemas.visits import VisitCountOut
from app.services import contact, visits

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])

DbSession = Annotated[Session, Depends(get_session)]
# Ids are Postgres `integer`: one out of range would be a 500 error in the database.
MessageId = Annotated[int, Path(ge=1, le=2**31 - 1)]


@router.get("/messages", response_model=list[ContactMessageOut])
def list_messages(session: DbSession) -> Sequence[ContactMessage]:
    return contact.list_messages(session)


@router.patch("/messages/{message_id}", response_model=ContactMessageOut)
def mark_message(
    message_id: MessageId, payload: MessageReadIn, session: DbSession
) -> ContactMessage:
    """Mark the message as read (`{"read": true}`) or unread. 404 if it doesn't exist."""
    return contact.set_read(session, message_id, payload.read)


@router.get("/visits")
def count_visits(session: DbSession) -> list[VisitCountOut]:
    return visits.count_by_utm(session)
