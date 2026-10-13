"""Formulario de contacto. Los largos calzan con las restricciones de la tabla `contact_message`.

El formulario es público, así que aquí se rechaza todo lo que no sea texto normal: caracteres
de control (que Postgres rechaza, como el byte nulo, o que permitirían inyectar cabeceras en el
correo de aviso) y campos que el formulario no envía.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.text import multiline, single_line

# Más estricto que la restricción de la base: exige un punto en el dominio y no deja pasar
# los separadores de direcciones (coma, punto y coma, <>, comillas), para que el Reply-To del
# correo de aviso tenga siempre una sola dirección.
_EMAIL_CHAR = r"[^@\s,;:<>()\[\]\\\"]"
EMAIL_PATTERN = rf"^{_EMAIL_CHAR}+@{_EMAIL_CHAR}+\.{_EMAIL_CHAR}+$"


def _optional_single_line(value: str | None) -> str | None:
    """Un texto vacío se guarda como `null`, igual que si no hubiera llegado."""
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
    """Lo que envía el formulario. Cualquier campo extra (como `read`) se rechaza."""

    model_config = ConfigDict(extra="forbid")

    name: Name
    email: Email
    message: Message
    lang: Literal["es", "en"]
    utm_source: Utm = None
    utm_campaign: Utm = None
    # Campo trampa (honeypot): el formulario lo oculta, así que una persona lo deja vacío.
    # Si llega con algo, es un bot: la API responde igual que siempre, pero no guarda nada.
    website: str = Field(default="", max_length=2000)


class ContactOut(BaseModel):
    status: Literal["ok"] = "ok"


# Panel: mensajes recibidos. Tienen datos personales del remitente: solo los ve el
# administrador con sesión y nunca van a los logs.


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
