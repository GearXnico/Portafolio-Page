"""Email sending over SMTP (Simple Mail Transfer Protocol), currently with Gmail
(ADR (Architecture Decision Record) 0005).

It is the only place that sends email: changing providers touches only this file.
"""

import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings

TIMEOUT_SECONDS = 10


class MailError(Exception):
    """The email could not be sent."""


def is_configured() -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_user
        and settings.smtp_password
        and settings.contact_notify_to
    )


def send_to_owner(*, subject: str, body: str, reply_to: str | None = None) -> None:
    """Send a plain-text email (no HTML) to `CONTACT_NOTIFY_TO`.

    Raises MailError if email is not configured or if the server fails.
    """
    # Same variables as is_configured(), read here so mypy knows they aren't None.
    # `assert` is not used, because Python skips it with `-O` (ruff rule S101).
    host, user, password = settings.smtp_host, settings.smtp_user, settings.smtp_password
    if not (host and user and password and settings.contact_notify_to):
        raise MailError("SMTP not configured")

    email = EmailMessage()
    email["From"] = user
    email["To"] = settings.contact_notify_to
    email["Subject"] = subject
    if reply_to:
        email["Reply-To"] = reply_to
    email.set_content(body)

    try:
        with smtplib.SMTP(host, settings.smtp_port, timeout=TIMEOUT_SECONDS) as smtp:
            # STARTTLS with certificate verification: the password never travels in plain text.
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(user, password.get_secret_value())
            smtp.send_message(email)
    except (smtplib.SMTPException, OSError) as exc:
        raise MailError(type(exc).__name__) from exc
