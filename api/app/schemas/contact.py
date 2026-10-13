"""Contact form. The lengths match the constraints of the `contact_message` table.

The form is public, so anything that isn't normal text is rejected here: control characters
(which Postgres rejects, like the null byte, or which would allow injecting headers into the
notice email) and fields the form doesn't send.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.text import multiline, single_line

# Stricter than the database constraint: it requires a dot in the domain and rejects address
# separators (comma, semicolon, <>, quotes), so the Reply-To of the notice email always has a
# single address.
_EMAIL_CHAR = r"[^@\s,;:<>()\[\]\\\"]"
EMAIL_PATTERN = rf"^{_EMAIL_CHAR}+@{_EMAIL_CHAR}+\.{_EMAIL_CHAR}+$"


def _optional_single_line(value: str | None) -> str | None:
    """An empty string is saved as `null`, the same as if it had not been sent."""
    return single_line(value) if value else None


Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    AfterValidator(single_line),
]
Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=320, pattern=EMAIL_PATTERN),
    AfterValidator(single_line),
]
Message = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
    AfterValidator(multiline),
]
Utm = Annotated[
    str | None,
    StringConstraints(strip_whitespace=True, max_length=200),
    AfterValidator(_optional_single_line),
]


class ContactIn(BaseModel):
    """What the form sends. Any extra field (like `read`) is rejected."""

    model_config = ConfigDict(extra="forbid")

    name: Name
    email: Email
    message: Message
    lang: Literal["es", "en"]
    utm_source: Utm = None
    utm_campaign: Utm = None
    # Trap field (honeypot): the form hides it, so a person leaves it empty.
    # If it arrives with something, it's a bot: the API responds as always, but saves nothing.
    website: str = Field(default="", max_length=2000)


class ContactOut(BaseModel):
    status: Literal["ok"] = "ok"


# Panel: received messages. They hold the sender's personal data: only the logged-in
# administrator sees them, and they never go to the logs.


class ContactMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    name: str
    email: str
    message: str
    lang: str
    utm_source: str | None
    utm_campaign: str | None
    read: bool


class MessageReadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    read: Annotated[bool, Field(strict=True)]
