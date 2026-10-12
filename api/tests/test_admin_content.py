"""Edición del contenido desde el panel: proyectos, perfil, habilidades y experiencia.

Contra el Postgres real: cada test corre en una transacción que se revierte al final.
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

from app.config import settings
from app.db import get_session
from app.main import MAX_BODY_BYTES, MAX_UPLOAD_BYTES, app
from app.models import Experience, Profile, Project, ProjectImage, Skill
from app.models.skill import SKILL_CATEGORIES
from app.routers.admin import COOKIE_NAME
from app.schemas.content import SkillCategory
from app.services import auth, images
from app.services.images import MAX_IMAGE_BYTES

PROYECTO: dict[str, Any] = {
    "slug": "mi-proyecto",
    "title_es": "Mi proyecto",
    "title_en": "My project",
    "summary_es": "Resumen",
    "summary_en": "Summary",
}
PERFIL: dict[str, Any] = {
    "headline_es": "Desarrollador",
    "headline_en": "Developer",
    "about_es": "Sobre mí",
    "about_en": "About me",
    "contact_email": "yo@example.com",
    "links": {"github": "https://github.com/ejemplo"},
}
HABILIDAD: dict[str, Any] = {"name": "Python", "category": "language"}
EXPERIENCIA: dict[str, Any] = {
    "company": "Empresa",
    "role_es": "Desarrollador",
    "role_en": "Developer",
    "start_date": "2024-01-01",
}


@pytest.fixture(autouse=True)
def admin_configurado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "admin_email", "admin@example.com")
    # Estos tests no hacen login: basta con que haya un hash.
    monkeypatch.setattr(settings, "admin_password_hash", SecretStr("$argon2id$no-se-usa"))
    monkeypatch.setattr(settings, "jwt_secret", SecretStr("s" * 48))


@pytest.fixture
def anonimo(db_session: Session) -> Iterator[TestClient]:
    """Cliente sin sesión. La API usa la sesión del test y parte con las tablas vacías."""
    for modelo in (ProjectImage, Project, Skill, Experience, Profile):
        db_session.execute(delete(modelo))

    def sesion_del_test() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = sesion_del_test
    # Por HTTPS, porque la cookie de sesión es Secure.
    with TestClient(app, base_url="https://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def admin(anonimo: TestClient) -> TestClient:
    """El mismo cliente, con la sesión del administrador."""
    anonimo.cookies.set(COOKIE_NAME, auth.create_session_token())
    return anonimo


def crear(admin: TestClient, ruta: str, datos: dict[str, Any], **cambios: Any) -> Any:
    response = admin.post(ruta, json=datos | cambios)
    assert response.status_code == 201, response.text
    return response.json()


# Acceso sin sesión: cada ruta de /api/admin/*, salvo login y logout.


def _rutas_protegidas() -> list[tuple[str, str]]:
    # Del esquema OpenAPI (la descripción de la API que genera FastAPI): trae todas las rutas
    # con sus métodos, incluidas las que se agreguen después.
    rutas = []
    for ruta, metodos in app.openapi()["paths"].items():
        if not ruta.startswith("/api/admin") or ruta in ("/api/admin/login", "/api/admin/logout"):
            continue
        for metodo in sorted(metodos):
            rutas.append((metodo.upper(), ruta.replace("{", "").replace("}", "")))
    return rutas


RUTAS_PROTEGIDAS = _rutas_protegidas()


def test_las_rutas_del_contenido_estan_en_la_lista() -> None:
    """Si alguien cambia los prefijos, la lista de abajo no puede quedar vacía sin avisar."""
    assert ("DELETE", "/api/admin/projects/project_id") in RUTAS_PROTEGIDAS
    assert ("PUT", "/api/admin/profile") in RUTAS_PROTEGIDAS
    assert ("POST", "/api/admin/projects/project_id/images") in RUTAS_PROTEGIDAS
    assert len(RUTAS_PROTEGIDAS) == 18


@pytest.mark.parametrize(("metodo", "ruta"), RUTAS_PROTEGIDAS)
def test_sin_sesion_responde_401(anonimo: TestClient, metodo: str, ruta: str) -> None:
    # Con un id que no existe y un cuerpo vacío: el 401 llega antes que el 404 o el 422,
    # así que sin sesión no se aprende nada del contenido ni del esquema.
    url = ruta
    for parametro in ("project_id", "image_id", "skill_id", "experience_id"):
        url = url.replace(parametro, "1")
    response = anonimo.request(metodo, url, json={})

    assert response.status_code == 401
    assert response.json() == {"detail": "Inicia sesión."}


def test_sin_sesion_no_cambia_nada(anonimo: TestClient, db_session: Session) -> None:
    anonimo.post("/api/admin/projects", json=PROYECTO)
    anonimo.put("/api/admin/profile", json=PERFIL)

    assert db_session.scalars(select(Project)).all() == []
    assert db_session.get(Profile, 1) is None


def test_una_sesion_invalida_responde_401(anonimo: TestClient) -> None:
    anonimo.cookies.set(COOKIE_NAME, "no-es-un-jwt")

    assert anonimo.get("/api/admin/projects").status_code == 401


# Proyectos


def test_crear_un_proyecto_lo_deja_oculto_y_con_valores_por_defecto(admin: TestClient) -> None:
    creado = crear(admin, "/api/admin/projects", PROYECTO)

    assert creado == PROYECTO | {
        "id": creado["id"],
        "body_es": "",
        "body_en": "",
        "stack": [],
        "demo_url": None,
        "repo_url": None,
        "visible": False,
        "position": 0,
        "images": [],
        "created_at": creado["created_at"],
        "updated_at": creado["updated_at"],
    }
    assert admin.get(f"/api/admin/projects/{creado['id']}").json() == creado


def test_la_lista_incluye_los_ocultos_en_orden(admin: TestClient) -> None:
    crear(admin, "/api/admin/projects", PROYECTO, slug="segundo", position=2)
    crear(admin, "/api/admin/projects", PROYECTO, slug="oculto", position=1)
    crear(admin, "/api/admin/projects", PROYECTO, slug="publicado", position=1, visible=True)

    lista = admin.get("/api/admin/projects").json()

    assert [p["slug"] for p in lista] == ["oculto", "publicado", "segundo"]


def test_editar_un_proyecto_reemplaza_todos_sus_campos(admin: TestClient) -> None:
    creado = crear(
        admin, "/api/admin/projects", PROYECTO, stack=["Python"], repo_url="https://github.com/x"
    )
    nuevo = PROYECTO | {
        "title_es": "  Otro título  ",
        "body_es": "# Cuerpo\n\nEn **Markdown**.",
        "visible": True,
        "position": 3,
    }

    response = admin.put(f"/api/admin/projects/{creado['id']}", json=nuevo)

    assert response.status_code == 200
    editado = response.json()
    assert editado["title_es"] == "Otro título"
    assert editado["body_es"] == "# Cuerpo\n\nEn **Markdown**."
    assert (editado["visible"], editado["position"]) == (True, 3)
    # Lo que no llega toma su valor por defecto.
    assert (editado["stack"], editado["repo_url"]) == ([], None)


def test_publicar_un_proyecto_lo_muestra_en_la_pagina(admin: TestClient) -> None:
    creado = crear(admin, "/api/admin/projects", PROYECTO)
    assert admin.get("/api/bootstrap").json()["projects"] == []

    admin.put(f"/api/admin/projects/{creado['id']}", json=PROYECTO | {"visible": True})

    assert [p["slug"] for p in admin.get("/api/bootstrap").json()["projects"]] == ["mi-proyecto"]


def test_borrar_un_proyecto_borra_sus_capturas(admin: TestClient, db_session: Session) -> None:
    creado = crear(admin, "/api/admin/projects", PROYECTO)
    db_session.add(ProjectImage(project_id=creado["id"], path="mi-proyecto/1.webp"))
    db_session.flush()

    assert admin.delete(f"/api/admin/projects/{creado['id']}").status_code == 204

    assert admin.get(f"/api/admin/projects/{creado['id']}").status_code == 404
    assert db_session.scalars(select(ProjectImage)).all() == []


def test_un_slug_repetido_responde_409(admin: TestClient) -> None:
    crear(admin, "/api/admin/projects", PROYECTO)
    otro = crear(admin, "/api/admin/projects", PROYECTO, slug="otro")

    al_crear = admin.post("/api/admin/projects", json=PROYECTO)
    al_editar = admin.put(f"/api/admin/projects/{otro['id']}", json=PROYECTO)

    for response in (al_crear, al_editar):
        assert response.status_code == 409
        assert response.json() == {"detail": "Ya existe un proyecto con ese slug."}
    # Después del error, la API sigue funcionando y el proyecto no cambió.
    assert admin.get(f"/api/admin/projects/{otro['id']}").json()["slug"] == "otro"


def test_un_enlace_vacio_se_guarda_como_null(admin: TestClient) -> None:
    creado = crear(admin, "/api/admin/projects", PROYECTO, demo_url="", repo_url="  ")

    assert (creado["demo_url"], creado["repo_url"]) == (None, None)


@pytest.mark.parametrize(
    "cambios",
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
        {"id": 5},
        {"created_at": "2020-01-01T00:00:00Z"},
    ],
)
def test_proyecto_invalido_responde_422(admin: TestClient, cambios: dict[str, Any]) -> None:
    response = admin.post("/api/admin/projects", json=PROYECTO | cambios)

    assert response.status_code == 422
    assert admin.get("/api/admin/projects").json() == []


def test_proyecto_sin_campos_obligatorios_responde_422(admin: TestClient) -> None:
    assert admin.post("/api/admin/projects", json={"slug": "solo-slug"}).status_code == 422


def test_un_proyecto_al_maximo_cabe_en_el_limite_de_la_api(admin: TestClient) -> None:
    """Con todos los campos al largo máximo y en caracteres de 2 bytes, no choca con el 413."""
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


@pytest.mark.parametrize(("metodo", "cuerpo"), [("GET", None), ("PUT", PROYECTO), ("DELETE", None)])
def test_proyecto_que_no_existe_responde_404(
    admin: TestClient, metodo: str, cuerpo: dict[str, Any] | None
) -> None:
    response = admin.request(metodo, "/api/admin/projects/999999", json=cuerpo)

    assert response.status_code == 404


# Perfil


def test_sin_perfil_responde_404(admin: TestClient) -> None:
    response = admin.get("/api/admin/profile")

    assert response.status_code == 404
    assert response.json() == {"detail": "Todavía no hay perfil."}


def test_el_primer_put_crea_el_perfil_y_los_siguientes_lo_reemplazan(admin: TestClient) -> None:
    assert admin.put("/api/admin/profile", json=PERFIL).status_code == 200

    nuevo = PERFIL | {"headline_es": "Desarrollador backend", "links": {}}
    response = admin.put("/api/admin/profile", json=nuevo)

    assert response.status_code == 200
    guardado = admin.get("/api/admin/profile").json()
    assert guardado == nuevo | {"updated_at": guardado["updated_at"]}


def test_el_correo_del_perfil_no_sale_en_la_pagina(admin: TestClient) -> None:
    admin.put("/api/admin/profile", json=PERFIL)

    perfil = admin.get("/api/bootstrap").json()["profile"]

    assert perfil["headline_es"] == "Desarrollador"
    assert "contact_email" not in perfil


@pytest.mark.parametrize(
    "cambios",
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
        {"id": 2},
    ],
)
def test_perfil_invalido_responde_422(admin: TestClient, cambios: dict[str, Any]) -> None:
    response = admin.put("/api/admin/profile", json=PERFIL | cambios)

    assert response.status_code == 422
    assert admin.get("/api/admin/profile").status_code == 404


# Habilidades


def test_crud_de_habilidades(admin: TestClient) -> None:
    python = crear(admin, "/api/admin/skills", HABILIDAD, position=1)
    fastapi = crear(admin, "/api/admin/skills", HABILIDAD, name="FastAPI", category="framework")
    assert python == HABILIDAD | {"id": python["id"], "position": 1}
    assert [s["name"] for s in admin.get("/api/admin/skills").json()] == ["FastAPI", "Python"]

    response = admin.put(f"/api/admin/skills/{fastapi['id']}", json=HABILIDAD | {"position": 2})
    assert response.json() == HABILIDAD | {"id": fastapi["id"], "position": 2}

    assert admin.delete(f"/api/admin/skills/{python['id']}").status_code == 204
    assert [s["id"] for s in admin.get("/api/admin/skills").json()] == [fastapi["id"]]


def test_las_categorias_calzan_con_la_base() -> None:
    assert get_args(SkillCategory) == SKILL_CATEGORIES


@pytest.mark.parametrize(
    "cambios",
    [
        {"category": "idioma"},
        {"name": ""},
        {"name": "a" * 101},
        {"position": True},
        {"id": 1},
    ],
)
def test_habilidad_invalida_responde_422(admin: TestClient, cambios: dict[str, Any]) -> None:
    assert admin.post("/api/admin/skills", json=HABILIDAD | cambios).status_code == 422


@pytest.mark.parametrize(("metodo", "cuerpo"), [("PUT", HABILIDAD), ("DELETE", None)])
def test_habilidad_que_no_existe_responde_404(
    admin: TestClient, metodo: str, cuerpo: dict[str, Any] | None
) -> None:
    assert admin.request(metodo, "/api/admin/skills/999999", json=cuerpo).status_code == 404


# Experiencia


def test_crud_de_experiencia(admin: TestClient) -> None:
    actual = crear(admin, "/api/admin/experience", EXPERIENCIA, start_date="2025-03-01")
    anterior = crear(
        admin, "/api/admin/experience", EXPERIENCIA, company="Antes", end_date="2025-02-28"
    )
    assert actual["end_date"] is None
    # Mismo orden que la página: por posición y, a igual posición, la más reciente primero.
    lista = admin.get("/api/admin/experience").json()
    assert [e["id"] for e in lista] == [actual["id"], anterior["id"]]

    cambios = EXPERIENCIA | {"description_es": "Hice\n- esto\n- y esto", "end_date": "2025-06-30"}
    editado = admin.put(f"/api/admin/experience/{actual['id']}", json=cambios).json()
    assert editado["description_es"] == "Hice\n- esto\n- y esto"
    assert editado["end_date"] == "2025-06-30"

    assert admin.delete(f"/api/admin/experience/{anterior['id']}").status_code == 204
    assert [e["id"] for e in admin.get("/api/admin/experience").json()] == [actual["id"]]


def test_una_experiencia_puede_empezar_y_terminar_el_mismo_dia(admin: TestClient) -> None:
    crear(admin, "/api/admin/experience", EXPERIENCIA, end_date=EXPERIENCIA["start_date"])


@pytest.mark.parametrize(
    "cambios",
    [
        {"end_date": "2023-12-31"},
        {"start_date": "no-es-fecha"},
        {"start_date": None},
        {"company": "una\nempresa"},
        {"description_en": "a" * 5001},
        {"position": -1},
    ],
)
def test_experiencia_invalida_responde_422(
    admin: TestClient, db_session: Session, cambios: dict[str, Any]
) -> None:
    response = admin.post("/api/admin/experience", json=EXPERIENCIA | cambios)

    assert response.status_code == 422
    assert db_session.scalars(select(Experience)).all() == []


@pytest.mark.parametrize(("metodo", "cuerpo"), [("PUT", EXPERIENCIA), ("DELETE", None)])
def test_experiencia_que_no_existe_responde_404(
    admin: TestClient, metodo: str, cuerpo: dict[str, Any] | None
) -> None:
    assert admin.request(metodo, "/api/admin/experience/999999", json=cuerpo).status_code == 404


def test_la_fecha_se_guarda_como_fecha(admin: TestClient, db_session: Session) -> None:
    creado = crear(admin, "/api/admin/experience", EXPERIENCIA)

    guardado = db_session.get(Experience, creado["id"])
    assert guardado is not None
    assert guardado.start_date == date(2024, 1, 1)


@pytest.mark.parametrize("ruta", ["projects", "skills", "experience"])
@pytest.mark.parametrize("item_id", ["0", "-1", str(2**31), "abc"])
def test_un_id_fuera_de_rango_responde_422(admin: TestClient, ruta: str, item_id: str) -> None:
    """Postgres usa `integer`: un id más grande no debe llegar a la base (sería un 500)."""
    assert admin.delete(f"/api/admin/{ruta}/{item_id}").status_code == 422


# Capturas de los proyectos


@pytest.fixture(autouse=True)
def media(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Cada test guarda las capturas en su propia carpeta temporal."""
    monkeypatch.setattr(settings, "media_dir", tmp_path)
    return tmp_path


def imagen(
    formato: str = "PNG",
    tamano: tuple[int, int] = (40, 30),
    modo: str = "RGB",
    color: str | tuple[int, ...] = "red",
) -> bytes:
    salida = io.BytesIO()
    Image.new(modo, tamano, color).save(salida, format=formato)
    return salida.getvalue()


def subir(
    cliente: TestClient,
    project_id: int,
    contenido: bytes,
    nombre: str = "captura.png",
    tipo: str = "image/png",
    **textos: str,
) -> Response:
    return cliente.post(
        f"/api/admin/projects/{project_id}/images",
        files={"file": (nombre, contenido, tipo)},
        data=textos,
    )


def archivos(carpeta: Path) -> list[Path]:
    return [ruta for ruta in carpeta.rglob("*") if ruta.is_file()]


@pytest.fixture
def proyecto(admin: TestClient) -> Any:
    return crear(admin, "/api/admin/projects", PROYECTO)


@pytest.mark.parametrize("formato", ["PNG", "JPEG", "WEBP"])
def test_una_imagen_valida_se_guarda_como_webp(
    admin: TestClient, proyecto: Any, media: Path, formato: str
) -> None:
    response = subir(admin, proyecto["id"], imagen(formato), alt_es="Inicio", alt_en="Home")

    assert response.status_code == 201, response.text
    captura = response.json()
    assert captura == {
        "id": captura["id"],
        "url": captura["url"],
        "alt_es": "Inicio",
        "alt_en": "Home",
        "position": 0,
    }
    assert re.fullmatch(r"/media/projects/[0-9a-f]{32}\.webp", captura["url"])
    [guardado] = archivos(media)
    assert guardado == media / captura["url"].removeprefix("/media/")
    with Image.open(guardado) as webp:
        assert (webp.format, webp.size) == ("WEBP", (40, 30))
    assert admin.get(f"/api/admin/projects/{proyecto['id']}").json()["images"] == [captura]


def test_la_captura_sale_en_la_pagina_publica(admin: TestClient, proyecto: Any) -> None:
    admin.put(f"/api/admin/projects/{proyecto['id']}", json=PROYECTO | {"visible": True})
    captura = subir(admin, proyecto["id"], imagen(), alt_es="Inicio").json()

    [publico] = admin.get("/api/bootstrap").json()["projects"]
    assert publico["images"] == [{"url": captura["url"], "alt_es": "Inicio", "alt_en": ""}]


def test_el_nombre_del_archivo_lo_pone_el_servidor(
    admin: TestClient, proyecto: Any, media: Path
) -> None:
    response = subir(admin, proyecto["id"], imagen(), nombre="../../app/main.py")

    assert response.status_code == 201
    assert "main" not in response.json()["url"]
    assert [ruta.parent for ruta in archivos(media)] == [media / "projects"]


def test_las_capturas_quedan_al_final_en_orden(admin: TestClient, proyecto: Any) -> None:
    for _ in range(3):
        subir(admin, proyecto["id"], imagen())

    capturas = admin.get(f"/api/admin/projects/{proyecto['id']}").json()["images"]
    assert [c["position"] for c in capturas] == [0, 1, 2]


@pytest.mark.parametrize(
    "contenido",
    [
        b"esto es texto, no una imagen",
        b"",
        b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        b"<?php system($_GET['c']); ?>",
        imagen("GIF"),
        imagen("BMP"),
    ],
    ids=["texto", "vacio", "svg", "php", "gif", "bmp"],
)
def test_un_archivo_que_no_es_imagen_aceptada_responde_415(
    admin: TestClient, proyecto: Any, media: Path, db_session: Session, contenido: bytes
) -> None:
    # El nombre y el tipo dicen PNG: solo cuenta el contenido.
    response = subir(admin, proyecto["id"], contenido)

    assert response.status_code == 415
    assert response.json() == {"detail": "El archivo no es una imagen JPEG, PNG o WebP."}
    assert archivos(media) == []
    assert db_session.scalars(select(ProjectImage)).all() == []


def test_una_imagen_de_mas_de_5_mb_responde_413(
    admin: TestClient, proyecto: Any, media: Path
) -> None:
    # Cabe en el límite del cuerpo (5 MB más el formulario), pero la imagen pasa los 5 MB.
    contenido = imagen() + b"\0" * MAX_IMAGE_BYTES

    response = subir(admin, proyecto["id"], contenido)

    assert response.status_code == 413
    assert response.json() == {"detail": "La captura supera los 5 MB."}
    assert archivos(media) == []


def test_una_imagen_de_5_mb_justos_se_acepta(admin: TestClient, proyecto: Any) -> None:
    # Pillow ignora los bytes que sobran después del final del PNG.
    contenido = imagen()
    contenido += b"\0" * (MAX_IMAGE_BYTES - len(contenido))

    assert subir(admin, proyecto["id"], contenido).status_code == 201


def test_un_cuerpo_mas_grande_que_el_limite_de_subida_responde_413(
    admin: TestClient, proyecto: Any
) -> None:
    response = subir(admin, proyecto["id"], b"\0" * MAX_UPLOAD_BYTES)

    assert response.status_code == 413
    assert response.json() == {"detail": "El cuerpo es demasiado grande"}


def test_el_limite_de_subida_no_aplica_a_las_demas_rutas(admin: TestClient) -> None:
    response = admin.post(
        "/api/admin/projects",
        content=b"{}" + b" " * MAX_BODY_BYTES,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413


def test_una_imagen_danada_responde_422(admin: TestClient, proyecto: Any, media: Path) -> None:
    ruido = Image.frombytes("RGB", (200, 200), os.urandom(200 * 200 * 3))
    salida = io.BytesIO()
    ruido.save(salida, format="PNG")
    cortada = salida.getvalue()[: len(salida.getvalue()) // 2]

    response = subir(admin, proyecto["id"], cortada)

    assert response.status_code == 422
    assert response.json() == {"detail": "La imagen está dañada o no se puede leer."}
    assert archivos(media) == []


@pytest.mark.parametrize("tamano", [(5000, 5001), (20_000, 20_000)], ids=["25mp", "bomba"])
def test_una_imagen_con_demasiados_pixeles_responde_422(
    admin: TestClient, proyecto: Any, media: Path, tamano: tuple[int, int]
) -> None:
    # En blanco y negro pesa pocos KB, pero abierta ocuparía cientos de MB.
    response = subir(admin, proyecto["id"], imagen(tamano=tamano, modo="1"))

    assert response.status_code == 422
    assert "demasiados píxeles" in response.json()["detail"]
    assert archivos(media) == []


def test_una_imagen_grande_se_achica_a_2560_px(
    admin: TestClient, proyecto: Any, media: Path
) -> None:
    subir(admin, proyecto["id"], imagen(tamano=(5120, 100)))

    with Image.open(archivos(media)[0]) as webp:
        assert webp.size == (2560, 50)


def test_la_transparencia_se_conserva(admin: TestClient, proyecto: Any, media: Path) -> None:
    subir(admin, proyecto["id"], imagen(modo="RGBA", color=(255, 0, 0, 128)))

    with Image.open(archivos(media)[0]) as webp:
        assert webp.mode == "RGBA"


def test_los_metadatos_se_descartan_y_se_respeta_la_rotacion(
    admin: TestClient, proyecto: Any, media: Path
) -> None:
    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = 6  # Girada 90°, como las fotos de celular.
    exif[ExifTags.Base.Make] = "Celular"
    salida = io.BytesIO()
    Image.new("RGB", (40, 30), "red").save(salida, format="JPEG", exif=exif)

    subir(admin, proyecto["id"], salida.getvalue())

    with Image.open(archivos(media)[0]) as webp:
        assert webp.size == (30, 40)
        assert "exif" not in webp.info
        assert len(webp.getexif()) == 0


@pytest.mark.parametrize(
    "textos",
    [{"alt_es": "a" * 301}, {"alt_en": "dos\nlíneas"}, {"alt_es": "\x00"}],
    ids=["largo", "salto", "control"],
)
def test_texto_alternativo_invalido_responde_422(
    admin: TestClient, proyecto: Any, media: Path, textos: dict[str, str]
) -> None:
    assert subir(admin, proyecto["id"], imagen(), **textos).status_code == 422
    assert archivos(media) == []


def test_subir_sin_archivo_responde_422(admin: TestClient, proyecto: Any) -> None:
    response = admin.post(f"/api/admin/projects/{proyecto['id']}/images", data={"alt_es": "x"})

    assert response.status_code == 422


def test_subir_a_un_proyecto_que_no_existe_responde_404(admin: TestClient, media: Path) -> None:
    assert subir(admin, 999_999, imagen()).status_code == 404
    assert archivos(media) == []


def test_subir_sin_sesion_no_guarda_el_archivo(
    anonimo: TestClient, db_session: Session, media: Path
) -> None:
    proyecto = Project(**PROYECTO)
    db_session.add(proyecto)
    db_session.flush()

    assert subir(anonimo, proyecto.id, imagen()).status_code == 401
    assert archivos(media) == []


def test_borrar_una_captura_borra_su_archivo(
    admin: TestClient, proyecto: Any, media: Path, db_session: Session
) -> None:
    captura = subir(admin, proyecto["id"], imagen()).json()

    url = f"/api/admin/projects/{proyecto['id']}/images/{captura['id']}"
    assert admin.delete(url).status_code == 204

    assert archivos(media) == []
    assert db_session.scalars(select(ProjectImage)).all() == []
    assert admin.delete(url).status_code == 404


def test_borrar_la_captura_de_otro_proyecto_responde_404(
    admin: TestClient, proyecto: Any, media: Path
) -> None:
    otro = crear(admin, "/api/admin/projects", PROYECTO, slug="otro")
    captura = subir(admin, proyecto["id"], imagen()).json()

    response = admin.delete(f"/api/admin/projects/{otro['id']}/images/{captura['id']}")

    assert response.status_code == 404
    assert len(archivos(media)) == 1


def test_borrar_un_proyecto_borra_los_archivos_de_sus_capturas(
    admin: TestClient, proyecto: Any, media: Path
) -> None:
    otro = crear(admin, "/api/admin/projects", PROYECTO, slug="otro")
    subir(admin, proyecto["id"], imagen())
    subir(admin, proyecto["id"], imagen())
    queda = subir(admin, otro["id"], imagen()).json()

    assert admin.delete(f"/api/admin/projects/{proyecto['id']}").status_code == 204

    assert archivos(media) == [media / queda["url"].removeprefix("/media/")]


def test_un_archivo_que_no_se_puede_borrar_queda_en_el_log(
    media: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # Una carpeta en lugar del archivo: unlink falla con un OSError.
    (media / "projects" / "carpeta.webp").mkdir(parents=True)

    images.remove_files(["projects/carpeta.webp", "projects/no-existe.webp"])

    assert "No se pudo borrar la captura projects/carpeta.webp" in caplog.text
