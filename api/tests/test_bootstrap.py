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
    """Client whose API uses the test's session: everything it writes is rolled back at the end.

    It starts with empty tables (inside the test's transaction), so the data in your local
    database doesn't change the result.
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
    # As in a real request, the API reads from the database and not from the objects in memory.
    db_session.expire_all()


# --- Lang ---


@pytest.mark.parametrize(
    ("headers", "params", "esperado"),
    [
        ({"Accept-Language": "es-CL,es;q=0.9,en;q=0.8"}, {}, "es"),
        ({"Accept-Language": "en-US,en;q=0.9"}, {}, "en"),
        ({}, {}, "en"),
        # The selector's choice wins over the browser.
        ({"Accept-Language": "en-US"}, {"lang": "es"}, "es"),
        ({"Accept-Language": "es-CL"}, {"lang": "en"}, "en"),
        # A `lang` that doesn't exist is ignored.
        ({"Accept-Language": "es-CL"}, {"lang": "fr"}, "es"),
    ],
)
def test_language(
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


# --- Content ---


def test_without_content_responds_empty(api: TestClient) -> None:
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
def test_returns_the_visible_content_in_both_languages(api: TestClient) -> None:
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
def test_hidden_projects_are_not_returned(api: TestClient) -> None:
    proyectos = api.get("/api/bootstrap").json()["projects"]

    assert [p["slug"] for p in proyectos] == ["primero", "publicado"]
    assert "borrador" not in api.get("/api/bootstrap").text


@pytest.mark.usefixtures("contenido")
def test_screenshots_come_in_order_and_with_their_url(api: TestClient) -> None:
    publicado = api.get("/api/bootstrap").json()["projects"][1]

    assert publicado["images"] == [
        {"url": "/media/publicado/1.webp", "alt_es": "Uno", "alt_en": "One"},
        {"url": "/media/publicado/2.webp", "alt_es": "Dos", "alt_en": "Two"},
    ]


@pytest.mark.usefixtures("contenido")
def test_does_not_expose_internal_data(api: TestClient) -> None:
    response = api.get("/api/bootstrap")
    datos = response.json()

    # Neither the contact email, nor ids, nor management fields.
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


def test_response_is_not_cached(api: TestClient) -> None:
    assert api.get("/api/bootstrap").headers["Cache-Control"] == "no-store"


# --- Visits and UTM ---


def test_records_the_visit_with_its_utm(api: TestClient, db_session: Session) -> None:
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


def test_without_utm_the_visit_has_no_source(api: TestClient, db_session: Session) -> None:
    api.get("/api/bootstrap")

    (visita,) = visitas(db_session)
    assert (visita.utm_source, visita.utm_medium, visita.utm_campaign, visita.utm_content) == (
        None,
        None,
        None,
        None,
    )
    assert visita.referrer is None


def test_long_or_garbage_utm_is_cleaned_without_breaking_the_page(
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
    # The text is stored as is: React escapes it when showing it in the panel.
    assert visita.utm_content == "<script>alert(1)</script>"
    assert visita.referrer is None


def test_does_not_store_the_ip_and_the_hash_identifies_the_visitor_of_the_day(
    api: TestClient, db_session: Session
) -> None:
    firefox = {"User-Agent": "Firefox/140"}
    api.get("/api/bootstrap", headers=firefox)
    api.get("/api/bootstrap", headers=firefox)
    api.get("/api/bootstrap", headers={"User-Agent": "Chrome/150"})

    hashes = [v.visitor_hash for v in visitas(db_session)]
    assert hashes[0] == hashes[1] != hashes[2]
    # The TestClient connects from "testclient": neither that value nor any other IP is in the row.
    for visita in visitas(db_session):
        valores = [str(getattr(visita, c.key)) for c in Visit.__table__.columns]
        assert not any("testclient" in v for v in valores)
    assert db_session.scalar(select(VisitorSalt.day)) is not None


def test_if_recording_fails_the_page_still_loads(
    api: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sqlalchemy.exc import OperationalError

    from app.routers import bootstrap

    def falla(*_: object, **__: object) -> None:
        raise OperationalError("INSERT", {}, Exception("the database is not responding"))

    monkeypatch.setattr(bootstrap, "daily_salt", falla)

    response = api.get("/api/bootstrap")

    assert response.status_code == 200
    assert visitas(db_session) == []
