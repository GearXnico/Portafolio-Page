"""Envío de correo por SMTP (protocolo de envío de correo), hoy con Gmail (ADR 0005).

Es el único lugar que envía correo: cambiar de proveedor toca solo este archivo.
"""

import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings

TIMEOUT_SECONDS = 10


class MailError(Exception):
    """El correo no se pudo enviar."""


def is_configured() -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_user
        and settings.smtp_password
        and settings.contact_notify_to
    )


def send_to_owner(*, subject: str, body: str, reply_to: str | None = None) -> None:
    """Envía un correo de texto plano (sin HTML) a `CONTACT_NOTIFY_TO`.

    Lanza MailError si el correo no está configurado o si el servidor falla.
    """
    # Mismas variables que is_configured(), leídas aquí para que mypy sepa que no son None.
    # No se usa `assert`, porque Python lo omite con `-O` (regla S101 de ruff).
    host, user, password = settings.smtp_host, settings.smtp_user, settings.smtp_password
    if not (host and user and password and settings.contact_notify_to):
        raise MailError("SMTP sin configurar")

    email = EmailMessage()
    email["From"] = user
    email["To"] = settings.contact_notify_to
    email["Subject"] = subject
    if reply_to:
        email["Reply-To"] = reply_to
    email.set_content(body)

    try:
        with smtplib.SMTP(host, settings.smtp_port, timeout=TIMEOUT_SECONDS) as smtp:
            # STARTTLS con verificación del certificado: la clave nunca viaja en texto plano.
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(user, password.get_secret_value())
            smtp.send_message(email)
    except (smtplib.SMTPException, OSError) as exc:
        raise MailError(type(exc).__name__) from exc
