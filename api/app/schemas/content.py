"""Contenido del sitio que se edita desde el panel: proyectos, perfil, habilidades y experiencia.

Los esquemas `...In` son lo que manda el panel: rechazan campos de más (como `id` o
`created_at`), caracteres de control y enlaces que no sean https. Los largos máximos frenan
abusos y dejan cada request bajo el límite de cuerpo de la API (`MAX_BODY_BYTES`).
Los esquemas `...Out` son lo que devuelve el panel, con id, orden y visibilidad.
"""

from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from app.models.base import URL_MAX_LENGTH
from app.schemas.contact import EMAIL_PATTERN
from app.schemas.text import multiline, single_line

# El mismo patrón que la restricción de la base (URL_HTTPS_REGEX): solo https, con host y sin
# espacios, para que un `javascript:` nunca llegue a un <a href> de la página (XSS).
_URL_PATTERN = r"^https://[^\s/]+\S*$"


def _empty_as_none(value: object) -> object:
    """Un enlace vacío del formulario se guarda como `null`."""
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _strip(max_length: int, min_length: int = 1) -> StringConstraints:
    return StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length)


# Textos de una línea (títulos, nombres) y textos largos (con saltos de línea).
Line200 = Annotated[str, _strip(200), AfterValidator(single_line)]
Line100 = Annotated[str, _strip(100), AfterValidator(single_line)]
Line50 = Annotated[str, _strip(50), AfterValidator(single_line)]
Text500 = Annotated[str, _strip(500), AfterValidator(multiline)]
Text5000 = Annotated[str, _strip(5000), AfterValidator(multiline)]
OptionalText5000 = Annotated[str, _strip(5000, min_length=0), AfterValidator(multiline)]
# Cuerpo en Markdown de un proyecto.
OptionalText10000 = Annotated[str, _strip(10_000, min_length=0), AfterValidator(multiline)]

Url = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=URL_MAX_LENGTH, pattern=_URL_PATTERN),
    AfterValidator(single_line),
]
OptionalUrl = Annotated[Url | None, BeforeValidator(_empty_as_none)]
# Orden en la página: el menor va primero.
Position = Annotated[int, Field(strict=True, ge=0, le=1_000_000)]
# El slug va en la URL: minúsculas, números y guiones simples (igual que en la base).
Slug = Annotated[str, StringConstraints(max_length=100, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
# Nombre de un enlace del perfil, por ejemplo "github" o "linkedin".
LinkKey = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]{0,29}$")]
Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=320, pattern=EMAIL_PATTERN),
    AfterValidator(single_line),
]
# Los mismos valores que SKILL_CATEGORIES (lo revisa un test).
SkillCategory = Literal["language", "framework", "tool"]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Proyectos


class ProjectIn(_In):
    slug: Slug
    title_es: Line200
    title_en: Line200
    summary_es: Text500
    summary_en: Text500
    body_es: OptionalText10000 = ""
    body_en: OptionalText10000 = ""
    stack: list[Line50] = Field(default=[], max_length=30)
    demo_url: OptionalUrl = None
    repo_url: OptionalUrl = None
    # Oculto por defecto: se publica desde el panel cuando está listo.
    visible: Annotated[bool, Field(strict=True)] = False
    position: Position = 0


class ProjectOut(_Out):
    id: int
    slug: str
    title_es: str
    title_en: str
    summary_es: str
    summary_en: str
    body_es: str
    body_en: str
    stack: list[str]
    demo_url: str | None
    repo_url: str | None
    visible: bool
    position: int
    created_at: datetime
    updated_at: datetime


# Perfil (una sola fila)


class ProfileIn(_In):
    headline_es: Line200
    headline_en: Line200
    about_es: Text5000
    about_en: Text5000
    # Solo lo ve el panel: la página pública no lo muestra (el contacto es por el formulario).
    contact_email: Email
    links: dict[LinkKey, Url] = Field(default={}, max_length=10)


class ProfileOut(_Out):
    headline_es: str
    headline_en: str
    about_es: str
    about_en: str
    contact_email: str
    links: dict[str, str]
    updated_at: datetime


# Habilidades


class SkillIn(_In):
    name: Line100
    category: SkillCategory
    position: Position = 0


class SkillOut(_Out):
    id: int
    name: str
    category: str
    position: int


# Experiencia


class ExperienceIn(_In):
    company: Line200
    role_es: Line200
    role_en: Line200
    description_es: OptionalText5000 = ""
    description_en: OptionalText5000 = ""
    start_date: date
    # Vacío: el trabajo actual.
    end_date: date | None = None
    position: Position = 0

    @model_validator(mode="after")
    def _end_after_start(self) -> Self:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date no puede ser anterior a start_date")
        return self


class ExperienceOut(_Out):
    id: int
    company: str
    role_es: str
    role_en: str
    description_es: str
    description_en: str
    start_date: date
    end_date: date | None
    position: int
