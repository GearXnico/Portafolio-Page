"""Respuesta de `GET /api/bootstrap`.

Trae los textos en los dos idiomas para que el selector cambie de idioma sin otra llamada.
No incluye ids, fechas de edición, orden, visibilidad ni el correo de contacto: la página
no los necesita y no hay por qué publicarlos.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.idioma import Idioma


class _DesdeModelo(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PerfilPublico(_DesdeModelo):
    headline_es: str
    headline_en: str
    about_es: str
    about_en: str
    links: dict[str, str]


class HabilidadPublica(_DesdeModelo):
    name: str
    category: str


class ExperienciaPublica(_DesdeModelo):
    company: str
    role_es: str
    role_en: str
    description_es: str
    description_en: str
    start_date: date
    end_date: date | None


class CapturaPublica(BaseModel):
    url: str
    alt_es: str
    alt_en: str


class ProyectoPublico(BaseModel):
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
    images: list[CapturaPublica]


class Bootstrap(BaseModel):
    lang: Idioma
    # None mientras no se haya cargado el perfil desde el panel.
    profile: PerfilPublico | None
    skills: list[HabilidadPublica]
    experience: list[ExperienciaPublica]
    projects: list[ProyectoPublico]
