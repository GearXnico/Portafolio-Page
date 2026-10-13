"""SQLAlchemy models. Alembic uses `Base.metadata` to autogenerate migrations.

Importing this package registers every table in `Base.metadata`.
"""

from app.models.base import Base
from app.models.contact_message import ContactMessage
from app.models.experience import Experience
from app.models.profile import Profile
from app.models.project import Project, ProjectImage
from app.models.skill import Skill
from app.models.visit import Visit
from app.models.visitor_salt import VisitorSalt

__all__ = [
    "Base",
    "ContactMessage",
    "Experience",
    "Profile",
    "Project",
    "ProjectImage",
    "Skill",
    "Visit",
    "VisitorSalt",
]
