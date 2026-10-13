"""Contact messages: saving, email notice in the background and reading from the panel."""

import logging
from collections.abc import Callable, Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import ContactMessage
from app.schemas.contact import ContactIn
from app.services import mail

# No personal data is logged: only the message id.
logger = logging.getLogger(__name__)


def save_message(session: Session, data: ContactIn) -> int:
    message = ContactMessage(
        name=data.name,
        email=data.email,
        message=data.message,
        lang=data.lang,
        utm_source=data.utm_source,
        utm_campaign=data.utm_campaign,
    )
    session.add(message)
    session.flush()
    message_id = message.id
    session.commit()
    return message_id


def notify_new_message(
    message_id: int, session_factory: Callable[[], Session] = SessionLocal
) -> None:
    """Send the email notice and set `emailed`. If it fails, the message stays saved anyway."""
    if not mail.is_configured():
        logger.warning("Email notice disabled (SMTP not configured): message %d", message_id)
        return

    with session_factory() as session:
        message = session.get(ContactMessage, message_id)
        if message is None:
            return
        try:
            mail.send_to_owner(
                subject=f"Nuevo mensaje de contacto de {message.name[:80]}",
                body=_body(message),
                reply_to=message.email,
            )
        except mail.MailError as exc:
            logger.warning("Could not send the notice for message %d: %s", message_id, exc)
            return
        message.emailed = True
        session.commit()


def _body(message: ContactMessage) -> str:
    origen = ", ".join(filter(None, [message.utm_source, message.utm_campaign])) or "directo"
    return (
        f"Nombre: {message.name}\n"
        f"Correo: {message.email}\n"
        f"Idioma: {message.lang}\n"
        f"Origen: {origen}\n"
        f"\n{message.message}\n"
    )


def list_messages(session: Session) -> Sequence[ContactMessage]:
    """All messages, newest first."""
    query = select(ContactMessage).order_by(
        ContactMessage.created_at.desc(), ContactMessage.id.desc()
    )
    return session.scalars(query).all()


def set_read(session: Session, message_id: int, read: bool) -> ContactMessage:
    """Mark the message as read or unread. 404 if it doesn't exist."""
    message = session.get(ContactMessage, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    message.read = read
    session.commit()
    return message
