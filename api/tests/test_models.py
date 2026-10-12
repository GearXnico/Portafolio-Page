"""Restricciones de la base: lo que Postgres rechaza aunque la API tenga un error."""

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
    """Comprueba que la base rechaza el objeto por la restricción indicada."""
    session.add(objeto)
    with pytest.raises(IntegrityError, match=restriccion):
        session.flush()
    session.rollback()


# Perfil


def test_perfil_se_guarda_con_valores_por_defecto(db_session: Session) -> None:
    db_session.add(nuevo_perfil())
    db_session.flush()

    perfil = db_session.get_one(Profile, 1)
    assert perfil.links == {}
    assert perfil.updated_at.tzinfo is not None


def test_perfil_admite_una_sola_fila(db_session: Session) -> None:
    rechaza(db_session, nuevo_perfil(id=2), "ck_profile_single_row")


def test_perfil_exige_los_textos_en_los_dos_idiomas(db_session: Session) -> None:
    rechaza(db_session, nuevo_perfil(headline_en=None), "headline_en")


# Habilidades


def test_habilidad_con_categoria_valida(db_session: Session) -> None:
    db_session.add(Skill(name="Python", category="language"))
    db_session.flush()

    assert db_session.scalars(select(Skill.position)).one() == 0


def test_habilidad_rechaza_categoria_desconocida(db_session: Session) -> None:
    rechaza(db_session, Skill(name="Python", category="lenguaje"), "ck_skill_category")


def test_habilidad_rechaza_posicion_negativa(db_session: Session) -> None:
    rechaza(db_session, Skill(name="Python", category="tool", position=-1), "ck_skill_position")


# Experiencia


def test_experiencia_actual_sin_fecha_de_termino(db_session: Session) -> None:
    db_session.add(nueva_experiencia(end_date=None))
    db_session.flush()

    assert db_session.scalars(select(Experience.end_date)).one() is None


def test_experiencia_rechaza_termino_antes_del_inicio(db_session: Session) -> None:
    experiencia = nueva_experiencia(start_date=date(2024, 6, 1), end_date=date(2024, 1, 1))
    rechaza(db_session, experiencia, "ck_experience_dates")


# Proyectos y capturas


def test_proyecto_nuevo_queda_oculto_y_sin_stack(db_session: Session) -> None:
    db_session.add(nuevo_proyecto())
    db_session.flush()

    proyecto = db_session.scalars(select(Project)).one()
    db_session.refresh(proyecto)
    assert proyecto.visible is False
    assert proyecto.stack == []
    assert proyecto.created_at.tzinfo is not None


def test_proyecto_guarda_su_stack(db_session: Session) -> None:
    db_session.add(nuevo_proyecto(stack=["FastAPI", "React"]))
    db_session.flush()

    assert db_session.scalars(select(Project.stack)).one() == ["FastAPI", "React"]


def test_proyecto_rechaza_slug_repetido(db_session: Session) -> None:
    db_session.add(nuevo_proyecto("repetido"))
    db_session.flush()

    rechaza(db_session, nuevo_proyecto("repetido"), "uq_project_slug")


@pytest.mark.parametrize(
    "slug", ["Con-Mayusculas", "con espacio", "-al-inicio", "doble--guion", ""]
)
def test_proyecto_rechaza_slug_invalido(db_session: Session, slug: str) -> None:
    rechaza(db_session, nuevo_proyecto(slug), "ck_project_slug_format")


def test_capturas_se_ordenan_por_posicion(db_session: Session) -> None:
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


def test_borrar_un_proyecto_borra_sus_capturas_en_la_base(db_session: Session) -> None:
    proyecto = nuevo_proyecto(images=[ProjectImage(path="a.webp")])
    db_session.add(proyecto)
    db_session.flush()

    # Borrado directo en SQL, sin pasar por el ORM: lo resuelve el ON DELETE CASCADE.
    db_session.execute(delete(Project).execution_options(synchronize_session=False))
    db_session.expire_all()

    assert db_session.scalars(select(ProjectImage)).all() == []


def test_captura_rechaza_proyecto_inexistente(db_session: Session) -> None:
    rechaza(
        db_session,
        ProjectImage(project_id=999_999, path="a.webp"),
        "fk_project_image_project_id_project",
    )


# Visitas


def test_visita_con_utm(db_session: Session) -> None:
    db_session.add(nueva_visita(utm_source="linkedin", utm_campaign="lanzamiento"))
    db_session.flush()

    visita = db_session.scalars(select(Visit)).one()
    assert (visita.utm_source, visita.utm_campaign) == ("linkedin", "lanzamiento")


def test_visita_rechaza_idioma_no_soportado(db_session: Session) -> None:
    rechaza(db_session, nueva_visita(lang="fr"), "ck_visit_lang")


@pytest.mark.parametrize("hash_", ["192.168.0.1", "A" * 64, "a" * 63])
def test_visita_solo_guarda_un_hash_sha256(db_session: Session, hash_: str) -> None:
    rechaza(db_session, nueva_visita(visitor_hash=hash_), "ck_visit_visitor_hash")


# Mensajes de contacto


def test_mensaje_nuevo_no_leido_ni_enviado(db_session: Session) -> None:
    db_session.add(nuevo_mensaje())
    db_session.flush()

    mensaje = db_session.scalars(select(ContactMessage)).one()
    db_session.refresh(mensaje)
    assert (mensaje.read, mensaje.emailed) == (False, False)


def test_mensaje_rechaza_idioma_no_soportado(db_session: Session) -> None:
    rechaza(db_session, nuevo_mensaje(lang="pt"), "ck_contact_message_lang")


def test_mensaje_exige_el_texto(db_session: Session) -> None:
    rechaza(db_session, nuevo_mensaje(message=None), "message")
