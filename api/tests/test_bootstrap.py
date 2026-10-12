from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.main import app
from app.models import Experience, Profile, Project, ProjectImage, Skill, Visit, VisitorSalt


@pytest.fixture
def api(client: TestClient, db_session: Session) -> TestClient:
    """Cliente cuya API usa la sesión del test: todo lo que escribe se revierte al final.

    Parte con las tablas vacías (dentro de la transacción del test), para que los datos que
    tengas en tu base local no cambien el resultado.
    """
    for modelo in (Visit, ProjectImage, Project, Skill, Experience, Profile):
        db_session.execute(delete(modelo))

    def sesion_del_test() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = sesion_del_test
    return client


def visitas(db_session: Session) -> list[Visit]:
    return list(db_session.scalars(select(Visit).order_by(Visit.id)))


def proyecto(slug: str, *, visible: bool, position: int = 0) -> Project:
    return Project(
        slug=slug,
        title_es=f"Título {slug}",
        title_en=f"Title {slug}",
        summary_es="Resumen",
        summary_en="Summary",
        visible=visible,
        position=position,
    )


@pytest.fixture
def contenido(api: TestClient, db_session: Session) -> None:
    db_session.add(
        Profile(
            headline_es="Desarrollador",
            headline_en="Developer",
            about_es="Sobre mí",
            about_en="About me",
            contact_email="privado@ejemplo.cl",
            links={"github": "https://github.com/ejemplo"},
        )
    )
    db_session.add_all(
        [
            Skill(name="Python", category="language", position=1),
            Skill(name="FastAPI", category="framework", position=0),
            Experience(
                company="Empresa",
                role_es="Desarrollador",
                role_en="Developer",
                start_date=date(2024, 1, 1),
            ),
        ]
    )
    publicado = proyecto("publicado", visible=True, position=1)
    publicado.images = [
        ProjectImage(path="publicado/2.webp", alt_es="Dos", alt_en="Two", position=2),
        ProjectImage(path="publicado/1.webp", alt_es="Uno", alt_en="One", position=1),
    ]
    db_session.add_all(
        [publicado, proyecto("primero", visible=True), proyecto("borrador", visible=False)]
    )
    db_session.flush()
    # Como en un request real, la API lee de la base y no de los objetos en memoria.
    db_session.expire_all()


# --- Lang ---


@pytest.mark.parametrize(
    ("headers", "params", "esperado"),
    [
        ({"Accept-Language": "es-CL,es;q=0.9,en;q=0.8"}, {}, "es"),
        ({"Accept-Language": "en-US,en;q=0.9"}, {}, "en"),
        ({}, {}, "en"),
        # La elección del selector manda sobre el navegador.
        ({"Accept-Language": "en-US"}, {"lang": "es"}, "es"),
        ({"Accept-Language": "es-CL"}, {"lang": "en"}, "en"),
        # Un `lang` que no existe se ignora.
        ({"Accept-Language": "es-CL"}, {"lang": "fr"}, "es"),
    ],
)
def test_idioma(
    api: TestClient,
    db_session: Session,
    headers: dict[str, str],
    params: dict[str, str],
    esperado: str,
) -> None:
    response = api.get("/api/bootstrap", headers=headers, params=params)

    assert response.status_code == 200
    assert response.json()["lang"] == esperado
    assert visitas(db_session)[-1].lang == esperado


# --- Contenido ---


def test_sin_contenido_responde_vacio(api: TestClient) -> None:
    response = api.get("/api/bootstrap")

    assert response.status_code == 200
    assert response.json() == {
        "lang": "en",
        "profile": None,
        "skills": [],
        "experience": [],
        "projects": [],
    }


@pytest.mark.usefixtures("contenido")
def test_devuelve_el_contenido_visible_en_los_dos_idiomas(api: TestClient) -> None:
    datos = api.get("/api/bootstrap").json()

    assert datos["profile"] == {
        "headline_es": "Desarrollador",
        "headline_en": "Developer",
        "about_es": "Sobre mí",
        "about_en": "About me",
        "links": {"github": "https://github.com/ejemplo"},
    }
    assert [s["name"] for s in datos["skills"]] == ["FastAPI", "Python"]
    assert datos["experience"] == [
        {
            "company": "Empresa",
            "role_es": "Desarrollador",
            "role_en": "Developer",
            "description_es": "",
            "description_en": "",
            "start_date": "2024-01-01",
            "end_date": None,
        }
    ]


@pytest.mark.usefixtures("contenido")
def test_los_proyectos_ocultos_no_salen(api: TestClient) -> None:
    proyectos = api.get("/api/bootstrap").json()["projects"]

    assert [p["slug"] for p in proyectos] == ["primero", "publicado"]
    assert "borrador" not in api.get("/api/bootstrap").text


@pytest.mark.usefixtures("contenido")
def test_las_capturas_salen_en_orden_y_con_su_url(api: TestClient) -> None:
    publicado = api.get("/api/bootstrap").json()["projects"][1]

    assert publicado["images"] == [
        {"url": "/media/publicado/1.webp", "alt_es": "Uno", "alt_en": "One"},
        {"url": "/media/publicado/2.webp", "alt_es": "Dos", "alt_en": "Two"},
    ]


@pytest.mark.usefixtures("contenido")
def test_no_expone_datos_internos(api: TestClient) -> None:
    response = api.get("/api/bootstrap")
    datos = response.json()

    # Ni el correo de contacto, ni ids, ni campos de gestión.
    assert "privado@ejemplo.cl" not in response.text
    internos = {"id", "visible", "position", "created_at", "updated_at", "project_id", "path"}
    for seccion in ("skills", "experience", "projects"):
        for item in datos[seccion]:
            assert internos.isdisjoint(item)
    assert set(datos["projects"][0]) == {
        "slug",
        "title_es",
        "title_en",
        "summary_es",
        "summary_en",
        "body_es",
        "body_en",
        "stack",
        "demo_url",
        "repo_url",
        "images",
    }


def test_la_respuesta_no_se_guarda_en_cache(api: TestClient) -> None:
    assert api.get("/api/bootstrap").headers["Cache-Control"] == "no-store"


# --- Visitas y UTM ---


def test_registra_la_visita_con_sus_utm(api: TestClient, db_session: Session) -> None:
    api.get(
        "/api/bootstrap",
        params={
            "utm_source": "linkedin",
            "utm_medium": "social",
            "utm_campaign": "postulacion-2026",
            "utm_content": "perfil",
            "referrer": "https://www.linkedin.com/in/alguien?trk=x",
        },
    )

    (visita,) = visitas(db_session)
    assert visita.utm_source == "linkedin"
    assert visita.utm_medium == "social"
    assert visita.utm_campaign == "postulacion-2026"
    assert visita.utm_content == "perfil"
    assert visita.referrer == "https://www.linkedin.com"
    assert visita.country is None


def test_sin_utm_la_visita_queda_sin_origen(api: TestClient, db_session: Session) -> None:
    api.get("/api/bootstrap")

    (visita,) = visitas(db_session)
    assert (visita.utm_source, visita.utm_medium, visita.utm_campaign, visita.utm_content) == (
        None,
        None,
        None,
        None,
    )
    assert visita.referrer is None


def test_utm_largos_o_con_basura_se_limpian_sin_romper_la_pagina(
    api: TestClient, db_session: Session
) -> None:
    response = api.get(
        "/api/bootstrap",
        params={
            "utm_source": "x" * 5000,
            "utm_medium": "so\x00cial\n",
            "utm_campaign": "   ",
            "utm_content": "<script>alert(1)</script>",
            "referrer": "javascript:alert(1)",
        },
    )

    assert response.status_code == 200
    (visita,) = visitas(db_session)
    assert visita.utm_source == "x" * 200
    assert visita.utm_medium == "social"
    assert visita.utm_campaign is None
    # El texto se guarda tal cual: React lo escapa al mostrarlo en el panel.
    assert visita.utm_content == "<script>alert(1)</script>"
    assert visita.referrer is None


def test_no_guarda_la_ip_y_el_hash_identifica_al_visitante_del_dia(
    api: TestClient, db_session: Session
) -> None:
    firefox = {"User-Agent": "Firefox/140"}
    api.get("/api/bootstrap", headers=firefox)
    api.get("/api/bootstrap", headers=firefox)
    api.get("/api/bootstrap", headers={"User-Agent": "Chrome/150"})

    hashes = [v.visitor_hash for v in visitas(db_session)]
    assert hashes[0] == hashes[1] != hashes[2]
    # El TestClient se conecta desde "testclient": ni ese valor ni otra IP quedan en la fila.
    for visita in visitas(db_session):
        valores = [str(getattr(visita, c.key)) for c in Visit.__table__.columns]
        assert not any("testclient" in v for v in valores)
    assert db_session.scalar(select(VisitorSalt.day)) is not None


def test_si_falla_el_registro_la_pagina_igual_carga(
    api: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sqlalchemy.exc import OperationalError

    from app.routers import bootstrap

    def falla(*_: object, **__: object) -> None:
        raise OperationalError("INSERT", {}, Exception("la base no responde"))

    monkeypatch.setattr(bootstrap, "daily_salt", falla)

    response = api.get("/api/bootstrap")

    assert response.status_code == 200
    assert visitas(db_session) == []
