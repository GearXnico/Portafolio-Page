"""Database constraints: what Postgres rejects even if the API has a bug."""

from datetime import date

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    ContactMessage,
    Experience,
    Profile,
    Project,
    ProjectImage,
    Skill,
    Visit,
)

VALID_HASH = "a" * 64


def new_profile(**changes: object) -> Profile:
    data: dict[str, object] = {
        "headline_es": "Desarrollador",
        "headline_en": "Developer",
        "about_es": "Hola",
        "about_en": "Hi",
        "contact_email": "yo@example.com",
    }
    return Profile(**(data | changes))


def new_project(slug: str = "mi-proyecto", **changes: object) -> Project:
    data: dict[str, object] = {
        "slug": slug,
        "title_es": "Título",
        "title_en": "Title",
        "summary_es": "Resumen",
        "summary_en": "Summary",
    }
    return Project(**(data | changes))


def new_experience(**changes: object) -> Experience:
    data: dict[str, object] = {
        "company": "Empresa",
        "role_es": "Desarrollador",
        "role_en": "Developer",
        "start_date": date(2024, 1, 1),
    }
    return Experience(**(data | changes))


def new_visit(**changes: object) -> Visit:
    data: dict[str, object] = {"lang": "es", "visitor_hash": VALID_HASH}
    return Visit(**(data | changes))


def new_message(**changes: object) -> ContactMessage:
    data: dict[str, object] = {
        "name": "Ana",
        "email": "ana@example.com",
        "message": "Hola",
        "lang": "es",
    }
    return ContactMessage(**(data | changes))


def rejects(session: Session, obj: object, constraint: str) -> None:
    """Check that the database rejects the object because of the given constraint."""
    session.add(obj)
    with pytest.raises(IntegrityError, match=constraint):
        session.flush()
    session.rollback()


# Profile


def test_profile_is_saved_with_default_values(db_session: Session) -> None:
    db_session.add(new_profile())
    db_session.flush()

    profile = db_session.get_one(Profile, 1)
    assert profile.links == {}
    assert profile.updated_at.tzinfo is not None


def test_profile_allows_a_single_row(db_session: Session) -> None:
    rejects(db_session, new_profile(id=2), "ck_profile_single_row")


def test_profile_requires_texts_in_both_languages(db_session: Session) -> None:
    rejects(db_session, new_profile(headline_en=None), "headline_en")


@pytest.mark.parametrize(
    "links",
    [
        {"github": "javascript:alert(1)"},
        {"cv": "http://example.com/cv.pdf"},
        {"linkedin": 123},
        {"github": ["https://github.com/x"]},
        {"github": "https://"},
        {"github": "https://github.com/x y"},
        ["https://github.com/x"],
    ],
)
def test_profile_only_accepts_https_links(db_session: Session, links: object) -> None:
    rejects(db_session, new_profile(links=links), "ck_profile_links_https")


def test_profile_accepts_https_links(db_session: Session) -> None:
    links = {"github": "https://github.com/x", "cv": "https://example.com/cv.pdf"}
    db_session.add(new_profile(links=links))
    db_session.flush()

    assert db_session.get_one(Profile, 1).links == links


# Skills


def test_skill_with_valid_category(db_session: Session) -> None:
    db_session.add(Skill(name="Python", category="language"))
    db_session.flush()

    assert db_session.scalars(select(Skill.position)).one() == 0


def test_skill_rejects_unknown_category(db_session: Session) -> None:
    rejects(db_session, Skill(name="Python", category="lenguaje"), "ck_skill_category")


def test_skill_rejects_negative_position(db_session: Session) -> None:
    rejects(db_session, Skill(name="Python", category="tool", position=-1), "ck_skill_position")


# Experience


def test_current_experience_without_end_date(db_session: Session) -> None:
    db_session.add(new_experience(end_date=None))
    db_session.flush()

    assert db_session.scalars(select(Experience.end_date)).one() is None


def test_one_day_experience(db_session: Session) -> None:
    db_session.add(new_experience(start_date=date(2024, 1, 1), end_date=date(2024, 1, 1)))
    db_session.flush()


def test_experience_rejects_end_before_start(db_session: Session) -> None:
    experience = new_experience(start_date=date(2024, 6, 1), end_date=date(2024, 1, 1))
    rejects(db_session, experience, "ck_experience_dates")


# Projects and screenshots


def test_new_project_is_hidden_and_without_stack(db_session: Session) -> None:
    db_session.add(new_project())
    db_session.flush()

    project = db_session.scalars(select(Project)).one()
    db_session.refresh(project)
    assert project.visible is False
    assert project.stack == []
    assert project.created_at.tzinfo is not None


def test_project_saves_its_stack(db_session: Session) -> None:
    db_session.add(new_project(stack=["FastAPI", "React"]))
    db_session.flush()

    assert db_session.scalars(select(Project.stack)).one() == ["FastAPI", "React"]


def test_project_rejects_duplicate_slug(db_session: Session) -> None:
    db_session.add(new_project("repetido"))
    db_session.flush()

    rejects(db_session, new_project("repetido"), "uq_project_slug")


@pytest.mark.parametrize(
    "slug", ["Con-Mayusculas", "con espacio", "-al-inicio", "doble--guion", ""]
)
def test_project_rejects_invalid_slug(db_session: Session, slug: str) -> None:
    rejects(db_session, new_project(slug), "ck_project_slug_format")


def test_screenshots_are_ordered_by_position(db_session: Session) -> None:
    project = new_project()
    project.images = [
        ProjectImage(path="b.webp", position=2),
        ProjectImage(path="a.webp", position=1),
    ]
    db_session.add(project)
    db_session.flush()
    db_session.expire_all()

    project = db_session.scalars(select(Project)).one()
    assert [image.path for image in project.images] == ["a.webp", "b.webp"]


def test_deleting_a_project_deletes_its_screenshots_in_the_database(db_session: Session) -> None:
    project = new_project(images=[ProjectImage(path="a.webp")])
    db_session.add(project)
    db_session.flush()

    # Direct delete in SQL, bypassing the ORM: ON DELETE CASCADE takes care of it.
    db_session.execute(delete(Project).execution_options(synchronize_session=False))
    db_session.expire_all()

    assert db_session.scalars(select(ProjectImage)).all() == []


def test_screenshot_rejects_nonexistent_project(db_session: Session) -> None:
    rejects(
        db_session,
        ProjectImage(project_id=999_999, path="a.webp"),
        "fk_project_image_project_id_project",
    )


# Visits


def test_visit_with_utm(db_session: Session) -> None:
    db_session.add(new_visit(utm_source="linkedin", utm_campaign="lanzamiento"))
    db_session.flush()

    visit = db_session.scalars(select(Visit)).one()
    assert (visit.utm_source, visit.utm_campaign) == ("linkedin", "lanzamiento")


def test_visit_rejects_unsupported_language(db_session: Session) -> None:
    rejects(db_session, new_visit(lang="fr"), "ck_visit_lang")


@pytest.mark.parametrize("hash_", ["192.168.0.1", "A" * 64, "a" * 63])
def test_visit_only_stores_a_sha256_hash(db_session: Session, hash_: str) -> None:
    rejects(db_session, new_visit(visitor_hash=hash_), "ck_visit_visitor_hash")


# Contact messages


def test_new_message_is_unread_and_not_emailed(db_session: Session) -> None:
    db_session.add(new_message())
    db_session.flush()

    message = db_session.scalars(select(ContactMessage)).one()
    db_session.refresh(message)
    assert (message.read, message.emailed) == (False, False)


def test_message_rejects_unsupported_language(db_session: Session) -> None:
    rejects(db_session, new_message(lang="pt"), "ck_contact_message_lang")


def test_message_requires_the_text(db_session: Session) -> None:
    rejects(db_session, new_message(message=None), "message")


# Limits on what comes from outside (defense in depth, on top of the API's validation)


@pytest.mark.parametrize("field", ["demo_url", "repo_url"])
@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "http://example.com",
        "//example.com",
        "https://",
        "https:///ruta",
        "https://example.com/con espacio",
        "https://example.com/\njavascript:alert(1)",
        "https://example.com/" + "a" * 2048,
    ],
)
def test_project_only_accepts_https_links(db_session: Session, field: str, url: str) -> None:
    rejects(db_session, new_project(**{field: url}), f"ck_project_{field}")


def test_project_accepts_https_links(db_session: Session) -> None:
    db_session.add(
        new_project(demo_url="https://demo.example.com", repo_url="https://github.com/x/y")
    )
    db_session.flush()


@pytest.mark.parametrize(
    "route", ["../etc/passwd", "/etc/passwd", "capturas/../../x.webp", "a\\b.webp", ".oculto"]
)
def test_screenshot_rejects_paths_outside_media(db_session: Session, route: str) -> None:
    project = new_project()
    db_session.add(project)
    db_session.flush()

    rejects(db_session, ProjectImage(project_id=project.id, path=route), "ck_project_image_path")


def test_screenshot_accepts_relative_path(db_session: Session) -> None:
    db_session.add(new_project(images=[ProjectImage(path="proyectos/1/captura-1.webp")]))
    db_session.flush()


@pytest.mark.parametrize(
    ("changes", "constraint"),
    [
        ({"name": ""}, "ck_contact_message_name_length"),
        ({"name": "a" * 201}, "ck_contact_message_name_length"),
        ({"email": "sin-arroba"}, "ck_contact_message_email"),
        ({"email": "a@b" + "c" * 320}, "ck_contact_message_email"),
        ({"message": ""}, "ck_contact_message_message_length"),
        ({"message": "a" * 5001}, "ck_contact_message_message_length"),
        ({"utm_source": "a" * 201}, "ck_contact_message_utm_length"),
    ],
)
def test_message_rejects_out_of_range_fields(
    db_session: Session, changes: dict[str, str], constraint: str
) -> None:
    rejects(db_session, new_message(**changes), constraint)


@pytest.mark.parametrize(
    ("changes", "constraint"),
    [
        ({"utm_medium": "a" * 201}, "ck_visit_utm_length"),
        ({"referrer": "https://" + "a" * 2048}, "ck_visit_referrer_length"),
        ({"country": "chile"}, "ck_visit_country"),
        ({"country": "cl"}, "ck_visit_country"),
    ],
)
def test_visit_rejects_out_of_range_fields(
    db_session: Session, changes: dict[str, str], constraint: str
) -> None:
    rejects(db_session, new_visit(**changes), constraint)


def test_visit_accepts_valid_country_and_referrer(db_session: Session) -> None:
    db_session.add(new_visit(country="CL", referrer="https://www.linkedin.com/"))
    db_session.flush()
