"""Modelos de SQLAlchemy. Alembic usa `Base.metadata` para autogenerar migraciones.

Importar este paquete registra todas las tablas en `Base.metadata`.
"""

from app.models.base import Base
from app.models.contact_message import ContactMessage
from app.models.experience import Experience
from app.models.profile import Profile
from app.models.project import Project, ProjectImage
from app.models.skill import Skill
from app.models.visit import Visit

__all__ = [
    "Base",
    "ContactMessage",
    "Experience",
    "Profile",
    "Project",
    "ProjectImage",
    "Skill",
    "Visit",
]
