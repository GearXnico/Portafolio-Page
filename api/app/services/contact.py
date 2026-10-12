"""Guardado de los mensajes de contacto y aviso por correo en segundo plano."""

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import ContactMessage
from app.schemas.contact import ContactIn
from app.services import mail

# No se registran datos personales: solo el id del mensaje.
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
    """Avisa por correo y marca `emailed`. Si falla, el mensaje queda guardado igual."""
    if not mail.is_configured():
        logger.warning("Aviso por correo desactivado (SMTP sin configurar): mensaje %d", message_id)
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
            logger.warning("No se pudo enviar el aviso del mensaje %d: %s", message_id, exc)
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
