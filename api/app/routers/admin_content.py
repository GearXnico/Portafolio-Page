"""Edición del contenido del sitio desde el panel: proyectos, perfil, habilidades y experiencia.

Todas las rutas exigen la sesión del administrador (`require_admin`, en el router completo).
Los cambios se ven en la página pública en la siguiente carga de `GET /api/bootstrap`.
"""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Path, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Experience, Profile, Project, ProjectImage, Skill
from app.routers.admin import require_admin
from app.schemas.content import (
    AltText,
    ExperienceIn,
    ExperienceOut,
    ImageOut,
    ProfileIn,
    ProfileOut,
    ProjectIn,
    ProjectOut,
    SkillIn,
    SkillOut,
)
from app.services import content, images

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])

DbSession = Annotated[Session, Depends(get_session)]
# Los ids son `integer` de Postgres: uno fuera de rango sería un error 500 en la base.
ItemId = Annotated[int, Path(ge=1, le=2**31 - 1)]


# Proyectos: el panel ve también los ocultos.


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(session: DbSession) -> Sequence[Project]:
    return content.list_ordered(session, Project, Project.position, Project.id)


@router.post("/projects", status_code=status.HTTP_201_CREATED, response_model=ProjectOut)
def create_project(payload: ProjectIn, session: DbSession) -> Project:
    """409 si el slug ya existe."""
    return content.create(session, Project, payload)


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: ItemId, session: DbSession) -> Project:
    return content.get_or_404(session, Project, project_id)


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: ItemId, payload: ProjectIn, session: DbSession) -> Project:
    """Reemplaza el proyecto completo, con su orden y visibilidad. 409 si el slug ya existe."""
    project = content.get_or_404(session, Project, project_id)
    return content.update(session, project, payload)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: ItemId, session: DbSession) -> None:
    """Borra el proyecto, sus capturas en la base y sus archivos."""
    project = content.get_or_404(session, Project, project_id)
    paths = [image.path for image in project.images]
    content.delete(session, project)
    images.remove_files(paths)


# Capturas de un proyecto: se suben como formulario (multipart) y se guardan en WebP.


@router.post(
    "/projects/{project_id}/images", status_code=status.HTTP_201_CREATED, response_model=ImageOut
)
def upload_image(
    project_id: ItemId,
    file: UploadFile,
    session: DbSession,
    alt_es: Annotated[AltText, Form()] = "",
    alt_en: Annotated[AltText, Form()] = "",
) -> ProjectImage:
    """JPEG, PNG o WebP de hasta 5 MB, detectado por su contenido. Queda al final del proyecto.

    413 si pesa más de 5 MB, 415 si no es una imagen aceptada y 422 si está dañada.
    """
    project = content.get_or_404(session, Project, project_id)
    return images.add_image(session, project, file.file, file.size, alt_es, alt_en)


@router.delete("/projects/{project_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(project_id: ItemId, image_id: ItemId, session: DbSession) -> None:
    """Borra la captura de la base y su archivo."""
    image = session.get(ProjectImage, image_id)
    if image is None or image.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe.")
    images.delete_image(session, image)


# Perfil: una sola fila, que se crea con el primer PUT.


@router.get("/profile", response_model=ProfileOut)
def get_profile(session: DbSession) -> Profile:
    """404 mientras no se haya guardado el perfil por primera vez."""
    profile = session.get(Profile, 1)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todavía no hay perfil.")
    return profile


@router.put("/profile", response_model=ProfileOut)
def save_profile(payload: ProfileIn, session: DbSession) -> Profile:
    return content.save_profile(session, payload)


# Habilidades


@router.get("/skills", response_model=list[SkillOut])
def list_skills(session: DbSession) -> Sequence[Skill]:
    return content.list_ordered(session, Skill, Skill.position, Skill.id)


@router.post("/skills", status_code=status.HTTP_201_CREATED, response_model=SkillOut)
def create_skill(payload: SkillIn, session: DbSession) -> Skill:
    return content.create(session, Skill, payload)


@router.put("/skills/{skill_id}", response_model=SkillOut)
def update_skill(skill_id: ItemId, payload: SkillIn, session: DbSession) -> Skill:
    return content.update(session, content.get_or_404(session, Skill, skill_id), payload)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: ItemId, session: DbSession) -> None:
    content.delete(session, content.get_or_404(session, Skill, skill_id))


# Experiencia: mismo orden que la página pública.


@router.get("/experience", response_model=list[ExperienceOut])
def list_experience(session: DbSession) -> Sequence[Experience]:
    return content.list_ordered(
        session, Experience, Experience.position, Experience.start_date.desc(), Experience.id
    )


@router.post("/experience", status_code=status.HTTP_201_CREATED, response_model=ExperienceOut)
def create_experience(payload: ExperienceIn, session: DbSession) -> Experience:
    return content.create(session, Experience, payload)


@router.put("/experience/{experience_id}", response_model=ExperienceOut)
def update_experience(
    experience_id: ItemId, payload: ExperienceIn, session: DbSession
) -> Experience:
    item = content.get_or_404(session, Experience, experience_id)
    return content.update(session, item, payload)


@router.delete("/experience/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(experience_id: ItemId, session: DbSession) -> None:
    content.delete(session, content.get_or_404(session, Experience, experience_id))
