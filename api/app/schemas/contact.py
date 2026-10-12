"""Formulario de contacto. Los largos calzan con las restricciones de la tabla `contact_message`.

El formulario es público, así que aquí se rechaza todo lo que no sea texto normal: caracteres
de control (que Postgres rechaza, como el byte nulo, o que permitirían inyectar cabeceras en el
correo de aviso) y campos que el formulario no envía.
"""

import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

# Caracteres de control (C0, DEL y C1) y los separadores de línea de Unicode.
_CONTROL = re.compile("[\x00-\x1f\x7f-\x9f  ]")
# En el mensaje se permiten saltos de línea y tabulaciones.
_CONTROL_MULTILINE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f  ]")
# Más estricto que la restricción de la base: exige un punto en el dominio y no deja pasar
# los separadores de direcciones (coma, punto y coma, <>, comillas), para que el Reply-To del
# correo de aviso tenga siempre una sola dirección.
_EMAIL_CHAR = r"[^@\s,;:<>()\[\]\\\"]"
EMAIL_PATTERN = rf"^{_EMAIL_CHAR}+@{_EMAIL_CHAR}+\.{_EMAIL_CHAR}+$"


def _single_line(value: str) -> str:
    if _CONTROL.search(value):
        raise ValueError("no puede tener saltos de línea ni caracteres de control")
    return value


def _multiline(value: str) -> str:
    if _CONTROL_MULTILINE.search(value):
        raise ValueError("no puede tener caracteres de control")
    return value


def _optional_single_line(value: str | None) -> str | None:
    """Un texto vacío se guarda como `null`, igual que si no hubiera llegado."""
    return _single_line(value) if value else None


Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    AfterValidator(_single_line),
]
Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=320, pattern=EMAIL_PATTERN),
    AfterValidator(_single_line),
]
Message = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
    AfterValidator(_multiline),
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
