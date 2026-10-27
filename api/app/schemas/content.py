"""Site content edited from the panel: projects, profile, skills and experience.

The `...In` schemas are what the panel sends: they reject extra fields (like `id` or
`created_at`), control characters and links that aren't https. The maximum lengths stop
abuse and keep each request under the API's body limit (`MAX_BODY_BYTES`).
The `...Out` schemas are what the panel gets back, with id, order and visibility.
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

# The same pattern as the database constraint (URL_HTTPS_REGEX): https only, with a host and no
# spaces, so a `javascript:` link never reaches an <a href> on the page.
_URL_PATTERN = r"^https://[^\s/]+\S*$"


def _empty_as_none(value: object) -> object:
    """An empty link from the form is saved as `null`."""
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _strip(max_length: int, min_length: int = 1) -> StringConstraints:
    return StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length)


# Single-line texts (titles, names) and long texts (with line breaks).
Line200 = Annotated[str, _strip(200), AfterValidator(single_line)]
Line100 = Annotated[str, _strip(100), AfterValidator(single_line)]
Line50 = Annotated[str, _strip(50), AfterValidator(single_line)]
Text500 = Annotated[str, _strip(500), AfterValidator(multiline)]
Text5000 = Annotated[str, _strip(5000), AfterValidator(multiline)]
OptionalText5000 = Annotated[str, _strip(5000, min_length=0), AfterValidator(multiline)]
# Markdown body of a project.
OptionalText10000 = Annotated[str, _strip(10_000, min_length=0), AfterValidator(multiline)]
# Alt text of a screenshot (for screen readers); empty if it is decorative.
AltText = Annotated[str, _strip(300, min_length=0), AfterValidator(single_line)]

Url = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=URL_MAX_LENGTH, pattern=_URL_PATTERN),
    AfterValidator(single_line),
]
OptionalUrl = Annotated[Url | None, BeforeValidator(_empty_as_none)]
Position = Annotated[int, Field(strict=True, ge=0, le=1_000_000)]
# The slug goes in the URL: lowercase letters, digits and single hyphens (same as the database).
Slug = Annotated[str, StringConstraints(max_length=100, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
# Name of a profile link, for example "github" or "linkedin".
LinkKey = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]{0,29}$")]
Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=320, pattern=EMAIL_PATTERN),
    AfterValidator(single_line),
]
# The same values as SKILL_CATEGORIES (a test checks it).
SkillCategory = Literal["language", "framework", "tool"]
# The same values as PROJECT_STATUSES (a test checks it).
ProjectStatus = Literal["done", "in_progress"]
# The same values as PALETTES (a test checks it).
Palette = Literal["mint", "ice", "neon-blue", "ice-neon", "glacier", "lavender", "crimson", "amber"]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


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
    status: ProjectStatus | None = None
    # Hidden by default: it is published from the panel when it's ready.
    visible: Annotated[bool, Field(strict=True)] = False
    position: Position = 0


class ImageOut(_Out):
    id: int
    url: str
    alt_es: str
    alt_en: str
    position: int


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
    status: str | None
    visible: bool
    position: int
    images: list[ImageOut]
    created_at: datetime
    updated_at: datetime


class ProfileIn(_In):
    headline_es: Line200
    headline_en: Line200
    about_es: Text5000
    about_en: Text5000
    # Only the panel sees it: the public page doesn't show it (contact goes through the form).
    contact_email: Email
    links: dict[LinkKey, Url] = Field(default={}, max_length=10)
    palette: Palette | None = None


class ProfileOut(_Out):
    headline_es: str
    headline_en: str
    about_es: str
    about_en: str
    contact_email: str
    links: dict[str, str]
    palette: str | None
    updated_at: datetime


class SkillIn(_In):
    name: Line100
    category: SkillCategory
    position: Position = 0


class SkillOut(_Out):
    id: int
    name: str
    category: str
    position: int


class ExperienceIn(_In):
    company: Line200
    role_es: Line200
    role_en: Line200
    description_es: OptionalText5000 = ""
    description_en: OptionalText5000 = ""
    start_date: date
    # Empty: the current job.
    end_date: date | None = None
    position: Position = 0

    @model_validator(mode="after")
    def _end_after_start(self) -> Self:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date can't be earlier than start_date")
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
