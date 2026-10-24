"""Editing the site content from the panel: projects, profile, skills and experience.

Every route requires the administrator's session (`require_admin`, on the whole router).
Changes show on the public page on the next load of `GET /api/bootstrap`.
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
# Ids are Postgres `integer`: one out of range would be a 500 error in the database.
ItemId = Annotated[int, Path(ge=1, le=2**31 - 1)]


# Projects: the panel also sees the hidden ones.


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(session: DbSession) -> Sequence[Project]:
    return content.list_ordered(session, Project, Project.position, Project.id)


@router.post("/projects", status_code=status.HTTP_201_CREATED, response_model=ProjectOut)
def create_project(payload: ProjectIn, session: DbSession) -> Project:
    """409 if the slug already exists."""
    return content.create(session, Project, payload)


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: ItemId, session: DbSession) -> Project:
    return content.get_or_404(session, Project, project_id)


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: ItemId, payload: ProjectIn, session: DbSession) -> Project:
    """Replace the whole project, with its order and visibility. 409 if the slug already exists."""
    project = content.get_or_404(session, Project, project_id)
    return content.update(session, project, payload)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: ItemId, session: DbSession) -> None:
    """Delete the project, its screenshots in the database and their files."""
    project = content.get_or_404(session, Project, project_id)
    paths = [image.path for image in project.images]
    content.delete(session, project)
    images.remove_files(paths)


# A project's screenshots: uploaded as a form (multipart) and saved as WebP.


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
    """JPEG, PNG or WebP up to 5 MB, detected by its content. It goes at the end of the project.

    413 if it weighs more than 5 MB, 415 if it isn't an accepted image and 422 if it's damaged.
    """
    project = content.get_or_404(session, Project, project_id)
    return images.add_image(session, project, file.file, file.size, alt_es, alt_en)


@router.delete("/projects/{project_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(project_id: ItemId, image_id: ItemId, session: DbSession) -> None:
    """Delete the screenshot from the database and its file."""
    image = session.get(ProjectImage, image_id)
    if image is None or image.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    images.delete_image(session, image)


# Profile: a single row, created with the first PUT.


@router.get("/profile", response_model=ProfileOut)
def get_profile(session: DbSession) -> Profile:
    """404 until the profile has been saved for the first time."""
    profile = session.get(Profile, 1)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="There is no profile yet."
        )
    return profile


@router.put("/profile", response_model=ProfileOut)
def save_profile(payload: ProfileIn, session: DbSession) -> Profile:
    return content.save_profile(session, payload)


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


# Experience: same order as the public page.


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
