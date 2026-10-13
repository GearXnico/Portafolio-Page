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

HASH_VALIDO = "a" * 64


def nuevo_perfil(**cambios: object) -> Profile:
    datos: dict[str, object] = {
        "headline_es": "Desarrollador",
        "headline_en": "Developer",
        "about_es": "Hola",
        "about_en": "Hi",
        "contact_email": "yo@example.com",
    }
    return Profile(**(datos | cambios))


def nuevo_proyecto(slug: str = "mi-proyecto", **cambios: object) -> Project:
    datos: dict[str, object] = {
        "slug": slug,
        "title_es": "Título",
        "title_en": "Title",
        "summary_es": "Resumen",
        "summary_en": "Summary",
    }
    return Project(**(datos | cambios))


def nueva_experiencia(**cambios: object) -> Experience:
    datos: dict[str, object] = {
        "company": "Empresa",
        "role_es": "Desarrollador",
        "role_en": "Developer",
        "start_date": date(2024, 1, 1),
    }
    return Experience(**(datos | cambios))


def nueva_visita(**cambios: object) -> Visit:
    datos: dict[str, object] = {"lang": "es", "visitor_hash": HASH_VALIDO}
    return Visit(**(datos | cambios))


def nuevo_mensaje(**cambios: object) -> ContactMessage:
    datos: dict[str, object] = {
        "name": "Ana",
        "email": "ana@example.com",
        "message": "Hola",
        "lang": "es",
    }
    return ContactMessage(**(datos | cambios))


def rechaza(session: Session, objeto: object, restriccion: str) -> None:
    """Check that the database rejects the object because of the given constraint."""
    session.add(objeto)
    with pytest.raises(IntegrityError, match=restriccion):
        session.flush()
    session.rollback()


# Profile


def test_profile_is_saved_with_default_values(db_session: Session) -> None:
    db_session.add(nuevo_perfil())
    db_session.flush()

    perfil = db_session.get_one(Profile, 1)
    assert perfil.links == {}
    assert perfil.updated_at.tzinfo is not None


def test_profile_allows_a_single_row(db_session: Session) -> None:
    rechaza(db_session, nuevo_perfil(id=2), "ck_profile_single_row")


def test_profile_requires_texts_in_both_languages(db_session: Session) -> None:
    rechaza(db_session, nuevo_perfil(headline_en=None), "headline_en")


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
    rechaza(db_session, nuevo_perfil(links=links), "ck_profile_links_https")


def test_profile_accepts_https_links(db_session: Session) -> None:
    links = {"github": "https://github.com/x", "cv": "https://example.com/cv.pdf"}
    db_session.add(nuevo_perfil(links=links))
    db_session.flush()

    assert db_session.get_one(Profile, 1).links == links


# Skills


def test_skill_with_valid_category(db_session: Session) -> None:
    db_session.add(Skill(name="Python", category="language"))
    db_session.flush()

    assert db_session.scalars(select(Skill.position)).one() == 0


def test_skill_rejects_unknown_category(db_session: Session) -> None:
    rechaza(db_session, Skill(name="Python", category="lenguaje"), "ck_skill_category")


def test_skill_rejects_negative_position(db_session: Session) -> None:
    rechaza(db_session, Skill(name="Python", category="tool", position=-1), "ck_skill_position")


# Experience


def test_current_experience_without_end_date(db_session: Session) -> None:
    db_session.add(nueva_experiencia(end_date=None))
    db_session.flush()

    assert db_session.scalars(select(Experience.end_date)).one() is None


def test_one_day_experience(db_session: Session) -> None:
    db_session.add(nueva_experiencia(start_date=date(2024, 1, 1), end_date=date(2024, 1, 1)))
    db_session.flush()


def test_experience_rejects_end_before_start(db_session: Session) -> None:
    experiencia = nueva_experiencia(start_date=date(2024, 6, 1), end_date=date(2024, 1, 1))
    rechaza(db_session, experiencia, "ck_experience_dates")


# Projects and screenshots


def test_new_project_is_hidden_and_without_stack(db_session: Session) -> None:
    db_session.add(nuevo_proyecto())
    db_session.flush()

    proyecto = db_session.scalars(select(Project)).one()
    db_session.refresh(proyecto)
    assert proyecto.visible is False
    assert proyecto.stack == []
    assert proyecto.created_at.tzinfo is not None


def test_project_saves_its_stack(db_session: Session) -> None:
    db_session.add(nuevo_proyecto(stack=["FastAPI", "React"]))
    db_session.flush()

    assert db_session.scalars(select(Project.stack)).one() == ["FastAPI", "React"]


def test_project_rejects_duplicate_slug(db_session: Session) -> None:
    db_session.add(nuevo_proyecto("repetido"))
    db_session.flush()

    rechaza(db_session, nuevo_proyecto("repetido"), "uq_project_slug")


@pytest.mark.parametrize(
    "slug", ["Con-Mayusculas", "con espacio", "-al-inicio", "doble--guion", ""]
)
def test_project_rejects_invalid_slug(db_session: Session, slug: str) -> None:
    rechaza(db_session, nuevo_proyecto(slug), "ck_project_slug_format")


def test_screenshots_are_ordered_by_position(db_session: Session) -> None:
    proyecto = nuevo_proyecto()
    proyecto.images = [
        ProjectImage(path="b.webp", position=2),
        ProjectImage(path="a.webp", position=1),
    ]
    db_session.add(proyecto)
    db_session.flush()
    db_session.expire_all()

    proyecto = db_session.scalars(select(Project)).one()
    assert [imagen.path for imagen in proyecto.images] == ["a.webp", "b.webp"]


def test_deleting_a_project_deletes_its_screenshots_in_the_database(db_session: Session) -> None:
    proyecto = nuevo_proyecto(images=[ProjectImage(path="a.webp")])
    db_session.add(proyecto)
    db_session.flush()

    # Direct delete in SQL, bypassing the ORM: ON DELETE CASCADE takes care of it.
    db_session.execute(delete(Project).execution_options(synchronize_session=False))
    db_session.expire_all()

    assert db_session.scalars(select(ProjectImage)).all() == []


def test_screenshot_rejects_nonexistent_project(db_session: Session) -> None:
    rechaza(
        db_session,
        ProjectImage(project_id=999_999, path="a.webp"),
        "fk_project_image_project_id_project",
    )


# Visits


def test_visit_with_utm(db_session: Session) -> None:
    db_session.add(nueva_visita(utm_source="linkedin", utm_campaign="lanzamiento"))
    db_session.flush()

    visita = db_session.scalars(select(Visit)).one()
    assert (visita.utm_source, visita.utm_campaign) == ("linkedin", "lanzamiento")


def test_visit_rejects_unsupported_language(db_session: Session) -> None:
    rechaza(db_session, nueva_visita(lang="fr"), "ck_visit_lang")


@pytest.mark.parametrize("hash_", ["192.168.0.1", "A" * 64, "a" * 63])
def test_visit_only_stores_a_sha256_hash(db_session: Session, hash_: str) -> None:
    rechaza(db_session, nueva_visita(visitor_hash=hash_), "ck_visit_visitor_hash")


# Contact messages


def test_new_message_is_unread_and_not_emailed(db_session: Session) -> None:
    db_session.add(nuevo_mensaje())
    db_session.flush()

    mensaje = db_session.scalars(select(ContactMessage)).one()
    db_session.refresh(mensaje)
    assert (mensaje.read, mensaje.emailed) == (False, False)


def test_message_rejects_unsupported_language(db_session: Session) -> None:
    rechaza(db_session, nuevo_mensaje(lang="pt"), "ck_contact_message_lang")


def test_message_requires_the_text(db_session: Session) -> None:
    rechaza(db_session, nuevo_mensaje(message=None), "message")


# Limits on what comes from outside (defense in depth, on top of the API's validation)


@pytest.mark.parametrize("campo", ["demo_url", "repo_url"])
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
def test_project_only_accepts_https_links(db_session: Session, campo: str, url: str) -> None:
    rechaza(db_session, nuevo_proyecto(**{campo: url}), f"ck_project_{campo}")


def test_project_accepts_https_links(db_session: Session) -> None:
    db_session.add(
        nuevo_proyecto(demo_url="https://demo.example.com", repo_url="https://github.com/x/y")
    )
    db_session.flush()


@pytest.mark.parametrize(
    "ruta", ["../etc/passwd", "/etc/passwd", "capturas/../../x.webp", "a\\b.webp", ".oculto"]
)
def test_screenshot_rejects_paths_outside_media(db_session: Session, ruta: str) -> None:
    proyecto = nuevo_proyecto()
    db_session.add(proyecto)
    db_session.flush()

    rechaza(db_session, ProjectImage(project_id=proyecto.id, path=ruta), "ck_project_image_path")


def test_screenshot_accepts_relative_path(db_session: Session) -> None:
    db_session.add(nuevo_proyecto(images=[ProjectImage(path="proyectos/1/captura-1.webp")]))
    db_session.flush()


@pytest.mark.parametrize(
    ("cambios", "restriccion"),
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
    db_session: Session, cambios: dict[str, str], restriccion: str
) -> None:
    rechaza(db_session, nuevo_mensaje(**cambios), restriccion)


@pytest.mark.parametrize(
    ("cambios", "restriccion"),
    [
        ({"utm_medium": "a" * 201}, "ck_visit_utm_length"),
        ({"referrer": "https://" + "a" * 2048}, "ck_visit_referrer_length"),
        ({"country": "chile"}, "ck_visit_country"),
        ({"country": "cl"}, "ck_visit_country"),
    ],
)
def test_visit_rejects_out_of_range_fields(
    db_session: Session, cambios: dict[str, str], restriccion: str
) -> None:
    rechaza(db_session, nueva_visita(**cambios), restriccion)


def test_visit_accepts_valid_country_and_referrer(db_session: Session) -> None:
    db_session.add(nueva_visita(country="CL", referrer="https://www.linkedin.com/"))
    db_session.flush()
