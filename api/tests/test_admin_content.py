"""Editing content from the panel: projects, profile, skills and experience.

Against the real Postgres: each test runs in a transaction that is rolled back at the end.
"""

import io
import os
import re
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any, get_args

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from PIL import ExifTags, Image
from pydantic import SecretStr
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from starlette.requests import Request as StarletteRequest

from app.config import settings
from app.db import get_session
from app.main import MAX_BODY_BYTES, MAX_UPLOAD_BYTES, app
from app.models import Experience, Profile, Project, ProjectImage, Skill
from app.models.profile import PALETTES
from app.models.project import PROJECT_STATUSES
from app.models.skill import SKILL_CATEGORIES
from app.routers.admin import COOKIE_NAME
from app.schemas.content import Palette, ProjectStatus, SkillCategory
from app.services import auth, images
from app.services.images import MAX_IMAGE_BYTES

PROJECT: dict[str, Any] = {
    "slug": "mi-proyecto",
    "title_es": "Mi proyecto",
    "title_en": "My project",
    "summary_es": "Resumen",
    "summary_en": "Summary",
}
PROFILE: dict[str, Any] = {
    "headline_es": "Desarrollador",
    "headline_en": "Developer",
    "about_es": "Sobre mí",
    "about_en": "About me",
    "contact_email": "yo@example.com",
    "links": {"github": "https://github.com/ejemplo"},
}
SKILL: dict[str, Any] = {"name": "Python", "category": "language"}
EXPERIENCE: dict[str, Any] = {
    "company": "Empresa",
    "role_es": "Desarrollador",
    "role_en": "Developer",
    "start_date": "2024-01-01",
}


@pytest.fixture(autouse=True)
def admin_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "admin_email", "admin@example.com")
    # These tests don't log in: having a hash is enough.
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr("$argon2id$no-se-usa"))
    monkeypatch.setattr(settings, "jwt_secret", SecretStr("s" * 48))


@pytest.fixture
def anonymous(db_session: Session) -> Iterator[TestClient]:
    """Client without a session. The API uses the test's session and starts with empty tables."""
    for model in (ProjectImage, Project, Skill, Experience, Profile):
        db_session.execute(delete(model))

    def test_session() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = test_session
    # Over HTTPS, because the session cookie is Secure.
    with TestClient(app, base_url="https://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def admin(anonymous: TestClient) -> TestClient:
    """The same client, with the administrator's session."""
    anonymous.cookies.set(COOKIE_NAME, auth.create_session_token())
    return anonymous


def create(admin: TestClient, route: str, data: dict[str, Any], **changes: Any) -> Any:
    response = admin.post(route, json=data | changes)
    assert response.status_code == 201, response.text
    return response.json()


# Access without a session: every /api/admin/* route, except login and logout.


def _protected_routes() -> list[tuple[str, str]]:
    # The OpenAPI schema lists every route with its methods, including ones added later.
    routes = []
    for route, methods in app.openapi()["paths"].items():
        if not route.startswith("/api/admin") or route in ("/api/admin/login", "/api/admin/logout"):
            continue
        for method in sorted(methods):
            routes.append((method.upper(), route.replace("{", "").replace("}", "")))
    return routes


PROTECTED_ROUTES = _protected_routes()


def test_content_routes_are_in_the_list() -> None:
    """If someone changes the prefixes, the list below can't silently end up empty."""
    assert ("DELETE", "/api/admin/projects/project_id") in PROTECTED_ROUTES
    assert ("PUT", "/api/admin/profile") in PROTECTED_ROUTES
    assert ("POST", "/api/admin/projects/project_id/images") in PROTECTED_ROUTES
    assert len(PROTECTED_ROUTES) == 21


@pytest.mark.parametrize(("method", "route"), PROTECTED_ROUTES)
def test_content_routes_without_session_respond_401(
    anonymous: TestClient, method: str, route: str
) -> None:
    # With an id that doesn't exist and an empty body: the 401 comes before the 404 or the 422,
    # so without a session nothing is learned about the content or the schema.
    url = route
    for param in ("project_id", "image_id", "skill_id", "experience_id", "message_id"):
        url = url.replace(param, "1")
    response = anonymous.request(method, url, json={})

    assert response.status_code == 401
    assert response.json() == {"detail": "Log in."}


def test_without_session_nothing_changes(anonymous: TestClient, db_session: Session) -> None:
    anonymous.post("/api/admin/projects", json=PROJECT)
    anonymous.put("/api/admin/profile", json=PROFILE)

    assert db_session.scalars(select(Project)).all() == []
    assert db_session.get(Profile, 1) is None


def test_an_invalid_session_responds_401(anonymous: TestClient) -> None:
    anonymous.cookies.set(COOKIE_NAME, "no-es-un-jwt")

    assert anonymous.get("/api/admin/projects").status_code == 401


# Projects


def test_creating_a_project_leaves_it_hidden_with_default_values(admin: TestClient) -> None:
    created = create(admin, "/api/admin/projects", PROJECT)

    assert created == PROJECT | {
        "id": created["id"],
        "body_es": "",
        "body_en": "",
        "stack": [],
        "demo_url": None,
        "repo_url": None,
        "status": None,
        "visible": False,
        "position": 0,
        "images": [],
        "created_at": created["created_at"],
        "updated_at": created["updated_at"],
    }
    assert admin.get(f"/api/admin/projects/{created['id']}").json() == created


def test_list_includes_hidden_ones_in_order(admin: TestClient) -> None:
    create(admin, "/api/admin/projects", PROJECT, slug="segundo", position=2)
    create(admin, "/api/admin/projects", PROJECT, slug="oculto", position=1)
    create(admin, "/api/admin/projects", PROJECT, slug="publicado", position=1, visible=True)

    listed = admin.get("/api/admin/projects").json()

    assert [p["slug"] for p in listed] == ["oculto", "publicado", "segundo"]


def test_editing_a_project_replaces_all_its_fields(admin: TestClient) -> None:
    created = create(
        admin, "/api/admin/projects", PROJECT, stack=["Python"], repo_url="https://github.com/x"
    )
    new = PROJECT | {
        "title_es": "  Otro título  ",
        "body_es": "# Cuerpo\n\nEn **Markdown**.",
        "visible": True,
        "position": 3,
    }

    response = admin.put(f"/api/admin/projects/{created['id']}", json=new)

    assert response.status_code == 200
    edited = response.json()
    assert edited["title_es"] == "Otro título"
    assert edited["body_es"] == "# Cuerpo\n\nEn **Markdown**."
    assert (edited["visible"], edited["position"]) == (True, 3)
    # Whatever isn't sent takes its default value.
    assert (edited["stack"], edited["repo_url"]) == ([], None)


def test_the_status_is_saved_and_shown_on_the_page(admin: TestClient) -> None:
    created = create(admin, "/api/admin/projects", PROJECT, status="in_progress", visible=True)
    assert admin.get("/api/bootstrap").json()["projects"][0]["status"] == "in_progress"

    # Like any other field, editing without a status clears it.
    admin.put(f"/api/admin/projects/{created['id']}", json=PROJECT | {"visible": True})

    assert admin.get("/api/bootstrap").json()["projects"][0]["status"] is None


def test_project_statuses_match_the_database() -> None:
    assert get_args(ProjectStatus) == PROJECT_STATUSES


def test_publishing_a_project_shows_it_on_the_page(admin: TestClient) -> None:
    created = create(admin, "/api/admin/projects", PROJECT)
    assert admin.get("/api/bootstrap").json()["projects"] == []

    admin.put(f"/api/admin/projects/{created['id']}", json=PROJECT | {"visible": True})

    assert [p["slug"] for p in admin.get("/api/bootstrap").json()["projects"]] == ["mi-proyecto"]


def test_deleting_a_project_deletes_its_screenshots(admin: TestClient, db_session: Session) -> None:
    created = create(admin, "/api/admin/projects", PROJECT)
    db_session.add(ProjectImage(project_id=created["id"], path="mi-proyecto/1.webp"))
    db_session.flush()

    assert admin.delete(f"/api/admin/projects/{created['id']}").status_code == 204

    assert admin.get(f"/api/admin/projects/{created['id']}").status_code == 404
    assert db_session.scalars(select(ProjectImage)).all() == []


def test_a_duplicate_slug_responds_409(admin: TestClient) -> None:
    create(admin, "/api/admin/projects", PROJECT)
    other = create(admin, "/api/admin/projects", PROJECT, slug="otro")

    on_create = admin.post("/api/admin/projects", json=PROJECT)
    on_edit = admin.put(f"/api/admin/projects/{other['id']}", json=PROJECT)

    for response in (on_create, on_edit):
        assert response.status_code == 409
        assert response.json() == {"detail": "A project with that slug already exists."}
    # After the error, the API keeps working and the project didn't change.
    assert admin.get(f"/api/admin/projects/{other['id']}").json()["slug"] == "otro"


def test_an_empty_link_is_saved_as_null(admin: TestClient) -> None:
    created = create(admin, "/api/admin/projects", PROJECT, demo_url="", repo_url="  ")

    assert (created["demo_url"], created["repo_url"]) == (None, None)


@pytest.mark.parametrize(
    "changes",
    [
        {"demo_url": "javascript:alert(1)"},
        {"demo_url": "http://example.com"},
        {"repo_url": "https://"},
        {"repo_url": "https://example.com/con espacio"},
        {"repo_url": "https://example.com/" + "a" * 2048},
        {"slug": "Mayusculas"},
        {"slug": "doble--guion"},
        {"slug": "-inicio"},
        {"slug": "a" * 101},
        {"title_es": ""},
        {"title_es": "   "},
        {"title_es": "dos\nlíneas"},
        {"title_en": "a" * 201},
        {"summary_es": ""},
        {"body_es": "byte nulo \x00"},
        {"body_en": "a" * 10_001},
        {"stack": ["a" * 51]},
        {"stack": ["x"] * 31},
        {"stack": "Python"},
        {"position": -1},
        {"position": 1_000_001},
        {"position": "1"},
        {"visible": "true"},
        {"status": "finished"},
        {"status": ""},
        {"id": 5},
        {"created_at": "2020-01-01T00:00:00Z"},
    ],
)
def test_invalid_project_responds_422(admin: TestClient, changes: dict[str, Any]) -> None:
    response = admin.post("/api/admin/projects", json=PROJECT | changes)

    assert response.status_code == 422
    assert admin.get("/api/admin/projects").json() == []


def test_project_without_mandatory_fields_responds_422(admin: TestClient) -> None:
    assert admin.post("/api/admin/projects", json={"slug": "solo-slug"}).status_code == 422


def test_a_maxed_out_project_fits_within_the_api_limit(admin: TestClient) -> None:
    """With every field at maximum length and in 2-byte characters, it doesn't hit the 413."""
    url = "https://example.com/" + "a" * (2048 - 20)
    response = admin.post(
        "/api/admin/projects",
        json={
            "slug": "a" * 100,
            "title_es": "ñ" * 200,
            "title_en": "ñ" * 200,
            "summary_es": "ñ" * 500,
            "summary_en": "ñ" * 500,
            "body_es": "ñ" * 10_000,
            "body_en": "ñ" * 10_000,
            "stack": ["ñ" * 50] * 30,
            "demo_url": url,
            "repo_url": url,
        },
    )

    assert response.status_code == 201
    assert int(response.request.headers["content-length"]) < MAX_BODY_BYTES


@pytest.mark.parametrize(("method", "body"), [("GET", None), ("PUT", PROJECT), ("DELETE", None)])
def test_nonexistent_project_responds_404(
    admin: TestClient, method: str, body: dict[str, Any] | None
) -> None:
    response = admin.request(method, "/api/admin/projects/999999", json=body)

    assert response.status_code == 404


# Profile


def test_without_profile_responds_404(admin: TestClient) -> None:
    response = admin.get("/api/admin/profile")

    assert response.status_code == 404
    assert response.json() == {"detail": "There is no profile yet."}


def test_first_put_creates_the_profile_and_later_ones_replace_it(admin: TestClient) -> None:
    assert admin.put("/api/admin/profile", json=PROFILE).status_code == 200

    new = PROFILE | {"headline_es": "Desarrollador backend", "links": {}, "palette": "amber"}
    response = admin.put("/api/admin/profile", json=new)

    assert response.status_code == 200
    saved = admin.get("/api/admin/profile").json()
    assert saved == new | {"updated_at": saved["updated_at"]}


def test_the_palette_reaches_the_page_and_defaults_to_none(admin: TestClient) -> None:
    admin.put("/api/admin/profile", json=PROFILE)
    assert admin.get("/api/bootstrap").json()["profile"]["palette"] is None

    admin.put("/api/admin/profile", json=PROFILE | {"palette": "ice"})

    assert admin.get("/api/bootstrap").json()["profile"]["palette"] == "ice"


def test_palettes_match_the_database() -> None:
    assert get_args(Palette) == PALETTES


def test_profile_email_is_not_shown_on_the_page(admin: TestClient) -> None:
    admin.put("/api/admin/profile", json=PROFILE)

    profile = admin.get("/api/bootstrap").json()["profile"]

    assert profile["headline_es"] == "Desarrollador"
    assert "contact_email" not in profile


@pytest.mark.parametrize(
    "changes",
    [
        {"links": {"github": "javascript:alert(1)"}},
        {"links": {"github": "http://github.com/x"}},
        {"links": {"github": 1}},
        {"links": {"GitHub": "https://github.com/x"}},
        {"links": {"<script>": "https://github.com/x"}},
        {"links": {f"k{i}": "https://example.com" for i in range(11)}},
        {"links": ["https://github.com/x"]},
        {"contact_email": "no-es-correo"},
        {"contact_email": "a@b.cl, c@d.cl"},
        {"about_es": ""},
        {"headline_en": "a" * 201},
        {"palette": "rojo"},
        {"palette": ""},
        {"id": 2},
    ],
)
def test_invalid_profile_responds_422(admin: TestClient, changes: dict[str, Any]) -> None:
    response = admin.put("/api/admin/profile", json=PROFILE | changes)

    assert response.status_code == 422
    assert admin.get("/api/admin/profile").status_code == 404


# Skills


def test_skills_crud(admin: TestClient) -> None:
    python = create(admin, "/api/admin/skills", SKILL, position=1)
    fastapi = create(admin, "/api/admin/skills", SKILL, name="FastAPI", category="framework")
    assert python == SKILL | {"id": python["id"], "position": 1}
    assert [s["name"] for s in admin.get("/api/admin/skills").json()] == ["FastAPI", "Python"]

    response = admin.put(f"/api/admin/skills/{fastapi['id']}", json=SKILL | {"position": 2})
    assert response.json() == SKILL | {"id": fastapi["id"], "position": 2}

    assert admin.delete(f"/api/admin/skills/{python['id']}").status_code == 204
    assert [s["id"] for s in admin.get("/api/admin/skills").json()] == [fastapi["id"]]


def test_categories_match_the_database() -> None:
    assert get_args(SkillCategory) == SKILL_CATEGORIES


@pytest.mark.parametrize(
    "changes",
    [
        {"category": "idioma"},
        {"name": ""},
        {"name": "a" * 101},
        {"position": True},
        {"id": 1},
    ],
)
def test_invalid_skill_responds_422(admin: TestClient, changes: dict[str, Any]) -> None:
    assert admin.post("/api/admin/skills", json=SKILL | changes).status_code == 422


@pytest.mark.parametrize(("method", "body"), [("PUT", SKILL), ("DELETE", None)])
def test_nonexistent_skill_responds_404(
    admin: TestClient, method: str, body: dict[str, Any] | None
) -> None:
    assert admin.request(method, "/api/admin/skills/999999", json=body).status_code == 404


# Experience


def test_experience_crud(admin: TestClient) -> None:
    current = create(admin, "/api/admin/experience", EXPERIENCE, start_date="2025-03-01")
    previous = create(
        admin, "/api/admin/experience", EXPERIENCE, company="Antes", end_date="2025-02-28"
    )
    assert current["end_date"] is None
    # Same order as the page: by position and, at equal position, the most recent first.
    listed = admin.get("/api/admin/experience").json()
    assert [e["id"] for e in listed] == [current["id"], previous["id"]]

    changes = EXPERIENCE | {"description_es": "Hice\n- esto\n- y esto", "end_date": "2025-06-30"}
    edited = admin.put(f"/api/admin/experience/{current['id']}", json=changes).json()
    assert edited["description_es"] == "Hice\n- esto\n- y esto"
    assert edited["end_date"] == "2025-06-30"

    assert admin.delete(f"/api/admin/experience/{previous['id']}").status_code == 204
    assert [e["id"] for e in admin.get("/api/admin/experience").json()] == [current["id"]]


def test_an_experience_can_start_and_end_on_the_same_day(admin: TestClient) -> None:
    create(admin, "/api/admin/experience", EXPERIENCE, end_date=EXPERIENCE["start_date"])


@pytest.mark.parametrize(
    "changes",
    [
        {"end_date": "2023-12-31"},
        {"start_date": "no-es-fecha"},
        {"start_date": None},
        {"company": "una\nempresa"},
        {"description_en": "a" * 5001},
        {"position": -1},
    ],
)
def test_invalid_experience_responds_422(
    admin: TestClient, db_session: Session, changes: dict[str, Any]
) -> None:
    response = admin.post("/api/admin/experience", json=EXPERIENCE | changes)

    assert response.status_code == 422
    assert db_session.scalars(select(Experience)).all() == []


@pytest.mark.parametrize(("method", "body"), [("PUT", EXPERIENCE), ("DELETE", None)])
def test_nonexistent_experience_responds_404(
    admin: TestClient, method: str, body: dict[str, Any] | None
) -> None:
    assert admin.request(method, "/api/admin/experience/999999", json=body).status_code == 404


def test_the_date_is_saved_as_a_date(admin: TestClient, db_session: Session) -> None:
    created = create(admin, "/api/admin/experience", EXPERIENCE)

    saved = db_session.get(Experience, created["id"])
    assert saved is not None
    assert saved.start_date == date(2024, 1, 1)


@pytest.mark.parametrize("route", ["projects", "skills", "experience"])
@pytest.mark.parametrize("item_id", ["0", "-1", str(2**31), "abc"])
def test_an_out_of_range_id_responds_422(admin: TestClient, route: str, item_id: str) -> None:
    """Postgres uses `integer`: a larger id must not reach the database (it would be a 500)."""
    assert admin.delete(f"/api/admin/{route}/{item_id}").status_code == 422


# Project screenshots


@pytest.fixture(autouse=True)
def media(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Each test saves the screenshots in its own temporary folder."""
    monkeypatch.setattr(settings, "media_dir", tmp_path)
    return tmp_path


def image(
    image_format: str = "PNG",
    size: tuple[int, int] = (40, 30),
    mode: str = "RGB",
    color: str | tuple[int, ...] = "red",
) -> bytes:
    output = io.BytesIO()
    Image.new(mode, size, color).save(output, format=image_format)
    return output.getvalue()


def upload(
    client: TestClient,
    project_id: int,
    content: bytes,
    name: str = "captura.png",
    kind: str = "image/png",
    **texts: str,
) -> Response:
    return client.post(
        f"/api/admin/projects/{project_id}/images",
        files={"file": (name, content, kind)},
        data=texts,
    )


def files(folder: Path) -> list[Path]:
    return [route for route in folder.rglob("*") if route.is_file()]


@pytest.fixture
def project(admin: TestClient) -> Any:
    return create(admin, "/api/admin/projects", PROJECT)


@pytest.mark.parametrize("image_format", ["PNG", "JPEG", "WEBP"])
def test_a_valid_image_is_saved_as_webp(
    admin: TestClient, project: Any, media: Path, image_format: str
) -> None:
    response = upload(admin, project["id"], image(image_format), alt_es="Inicio", alt_en="Home")

    assert response.status_code == 201, response.text
    screenshot = response.json()
    assert screenshot == {
        "id": screenshot["id"],
        "url": screenshot["url"],
        "alt_es": "Inicio",
        "alt_en": "Home",
        "position": 0,
    }
    assert re.fullmatch(r"/media/projects/[0-9a-f]{32}\.webp", screenshot["url"])
    [saved] = files(media)
    assert saved == media / screenshot["url"].removeprefix("/media/")
    with Image.open(saved) as webp:
        assert (webp.format, webp.size) == ("WEBP", (40, 30))
    assert admin.get(f"/api/admin/projects/{project['id']}").json()["images"] == [screenshot]


def test_the_screenshot_shows_on_the_public_page(admin: TestClient, project: Any) -> None:
    admin.put(f"/api/admin/projects/{project['id']}", json=PROJECT | {"visible": True})
    screenshot = upload(admin, project["id"], image(), alt_es="Inicio").json()

    [public] = admin.get("/api/bootstrap").json()["projects"]
    assert public["images"] == [{"url": screenshot["url"], "alt_es": "Inicio", "alt_en": ""}]


def test_the_server_sets_the_file_name(admin: TestClient, project: Any, media: Path) -> None:
    response = upload(admin, project["id"], image(), name="../../app/main.py")

    assert response.status_code == 201
    assert "main" not in response.json()["url"]
    assert [route.parent for route in files(media)] == [media / "projects"]


def test_screenshots_go_at_the_end_in_order(admin: TestClient, project: Any) -> None:
    for _ in range(3):
        upload(admin, project["id"], image())

    screenshots = admin.get(f"/api/admin/projects/{project['id']}").json()["images"]
    assert [c["position"] for c in screenshots] == [0, 1, 2]


@pytest.mark.parametrize(
    "content",
    [
        b"esto es texto, no una imagen",
        b"",
        b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        b"<?php system($_GET['c']); ?>",
        image("GIF"),
        image("BMP"),
    ],
    ids=["text", "empty", "svg", "php", "gif", "bmp"],
)
def test_a_file_that_is_not_an_accepted_image_responds_415(
    admin: TestClient, project: Any, media: Path, db_session: Session, content: bytes
) -> None:
    # The name and the type say PNG: only the content counts.
    response = upload(admin, project["id"], content)

    assert response.status_code == 415
    assert response.json() == {"detail": "The file is not a JPEG, PNG or WebP image."}
    assert files(media) == []
    assert db_session.scalars(select(ProjectImage)).all() == []


def test_an_image_over_5_mb_responds_413(admin: TestClient, project: Any, media: Path) -> None:
    # It fits the body limit (5 MB plus the form), but the image is over 5 MB.
    content = image() + b"\0" * MAX_IMAGE_BYTES

    response = upload(admin, project["id"], content)

    assert response.status_code == 413
    assert response.json() == {"detail": "The screenshot exceeds 5 MB."}
    assert files(media) == []


def test_an_image_of_exactly_5_mb_is_accepted(admin: TestClient, project: Any) -> None:
    # Pillow ignores the extra bytes after the end of the PNG.
    content = image()
    content += b"\0" * (MAX_IMAGE_BYTES - len(content))

    assert upload(admin, project["id"], content).status_code == 201


def test_a_body_larger_than_the_upload_limit_responds_413(admin: TestClient, project: Any) -> None:
    response = upload(admin, project["id"], b"\0" * MAX_UPLOAD_BYTES)

    assert response.status_code == 413
    assert response.json() == {"detail": "The body is too large"}


def test_the_upload_limit_only_accepts_numeric_ids(admin: TestClient) -> None:
    response = admin.post(
        "/api/admin/projects/abc/images", files={"file": ("a.png", b"\0" * MAX_BODY_BYTES)}
    )

    assert response.status_code == 413


def test_the_upload_limit_does_not_apply_to_other_routes(admin: TestClient) -> None:
    response = admin.post(
        "/api/admin/projects",
        content=b"{}" + b" " * MAX_BODY_BYTES,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413


def test_a_damaged_image_responds_422(admin: TestClient, project: Any, media: Path) -> None:
    noise = Image.frombytes("RGB", (200, 200), os.urandom(200 * 200 * 3))
    output = io.BytesIO()
    noise.save(output, format="PNG")
    cut = output.getvalue()[: len(output.getvalue()) // 2]

    response = upload(admin, project["id"], cut)

    assert response.status_code == 422
    assert response.json() == {"detail": "The image is damaged or can't be read."}
    assert files(media) == []


@pytest.mark.parametrize("size", [(5000, 5001), (20_000, 20_000)], ids=["25mp", "bomb"])
def test_an_image_with_too_many_pixels_responds_422(
    admin: TestClient, project: Any, media: Path, size: tuple[int, int]
) -> None:
    # In black and white it weighs a few KB, but opened it would take hundreds of MB.
    response = upload(admin, project["id"], image(size=size, mode="1"))

    assert response.status_code == 422
    assert "too many pixels" in response.json()["detail"]
    assert files(media) == []


def test_a_large_image_is_shrunk_to_2560_px(admin: TestClient, project: Any, media: Path) -> None:
    upload(admin, project["id"], image(size=(5120, 100)))

    with Image.open(files(media)[0]) as webp:
        assert webp.size == (2560, 50)


def test_transparency_is_kept(admin: TestClient, project: Any, media: Path) -> None:
    upload(admin, project["id"], image(mode="RGBA", color=(255, 0, 0, 128)))

    with Image.open(files(media)[0]) as webp:
        assert webp.mode == "RGBA"


def test_metadata_is_discarded_and_rotation_is_respected(
    admin: TestClient, project: Any, media: Path
) -> None:
    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = 6  # Rotated 90°, like phone photos.
    exif[ExifTags.Base.Make] = "Celular"
    output = io.BytesIO()
    Image.new("RGB", (40, 30), "red").save(output, format="JPEG", exif=exif)

    upload(admin, project["id"], output.getvalue())

    with Image.open(files(media)[0]) as webp:
        assert webp.size == (30, 40)
        assert "exif" not in webp.info
        assert len(webp.getexif()) == 0


@pytest.mark.parametrize(
    "texts",
    [{"alt_es": "a" * 301}, {"alt_en": "dos\nlíneas"}, {"alt_es": "\x00"}],
    ids=["long", "newline", "control"],
)
def test_invalid_alt_text_responds_422(
    admin: TestClient, project: Any, media: Path, texts: dict[str, str]
) -> None:
    assert upload(admin, project["id"], image(), **texts).status_code == 422
    assert files(media) == []


def test_uploading_without_a_file_responds_422(admin: TestClient, project: Any) -> None:
    response = admin.post(f"/api/admin/projects/{project['id']}/images", data={"alt_es": "x"})

    assert response.status_code == 422


def test_uploading_to_a_nonexistent_project_responds_404(admin: TestClient, media: Path) -> None:
    assert upload(admin, 999_999, image()).status_code == 404
    assert files(media) == []


def test_uploading_without_session_does_not_save_the_file(
    anonymous: TestClient, db_session: Session, media: Path
) -> None:
    project = Project(**PROJECT)
    db_session.add(project)
    db_session.flush()

    assert upload(anonymous, project.id, image()).status_code == 401
    assert files(media) == []


@pytest.mark.parametrize("cookie", [None, "no-es-un-jwt"], ids=["no-cookie", "invalid"])
def test_without_session_the_upload_does_not_read_the_form(
    anonymous: TestClient, monkeypatch: pytest.MonkeyPatch, cookie: str | None
) -> None:
    # FastAPI reads the form before checking the session: the middleware cuts it off first.
    read: list[bool] = []
    monkeypatch.setattr(StarletteRequest, "form", lambda *_a, **_k: read.append(True))
    if cookie:
        anonymous.cookies.set(COOKIE_NAME, cookie)

    response = upload(anonymous, 1, b"\0" * MAX_IMAGE_BYTES)

    assert response.status_code == 401
    assert response.json() == {"detail": "Log in."}
    assert read == []


def test_deleting_a_screenshot_deletes_its_file(
    admin: TestClient, project: Any, media: Path, db_session: Session
) -> None:
    screenshot = upload(admin, project["id"], image()).json()

    url = f"/api/admin/projects/{project['id']}/images/{screenshot['id']}"
    assert admin.delete(url).status_code == 204

    assert files(media) == []
    assert db_session.scalars(select(ProjectImage)).all() == []
    assert admin.delete(url).status_code == 404


def test_deleting_another_projects_screenshot_responds_404(
    admin: TestClient, project: Any, media: Path
) -> None:
    other = create(admin, "/api/admin/projects", PROJECT, slug="otro")
    screenshot = upload(admin, project["id"], image()).json()

    response = admin.delete(f"/api/admin/projects/{other['id']}/images/{screenshot['id']}")

    assert response.status_code == 404
    assert len(files(media)) == 1


def test_deleting_a_project_deletes_its_screenshot_files(
    admin: TestClient, project: Any, media: Path
) -> None:
    other = create(admin, "/api/admin/projects", PROJECT, slug="otro")
    upload(admin, project["id"], image())
    upload(admin, project["id"], image())
    remaining = upload(admin, other["id"], image()).json()

    assert admin.delete(f"/api/admin/projects/{project['id']}").status_code == 204

    assert files(media) == [media / remaining["url"].removeprefix("/media/")]


def test_a_file_that_cannot_be_deleted_is_logged(
    media: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # A folder instead of the file: unlink fails with an OSError.
    (media / "projects" / "carpeta.webp").mkdir(parents=True)

    images.remove_files(["projects/carpeta.webp", "projects/no-existe.webp"])

    assert "Could not delete the screenshot projects/carpeta.webp" in caplog.text
