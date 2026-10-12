# plantilla-producto

Plantilla para empezar productos web con pruebas, CI/CD (integración y despliegue continuos) y despliegue ya resueltos. Es un monorepo con tres piezas:

- **api/**: API (interfaz de programación) en Python con FastAPI.
- **web/**: frontend en React y TypeScript que se compila a archivos estáticos con Vite.
- **db**: Postgres 18.

En producción, Caddy sirve el frontend y pasa `/api` a la API, todo con Docker Compose en un VPS (servidor virtual privado).

> Estado: en construcción. La API y la web tienen su esqueleto (la página muestra si la API y la base responden), la base tiene las tablas del contenido (perfil, habilidades, experiencia, proyectos, capturas, visitas y mensajes) y la API ya entrega el contenido con `GET /api/bootstrap`, recibe mensajes de contacto, tiene el login del administrador y deja editar el contenido desde el panel.

## Requisitos

- Docker con Docker Compose v2.
- Git.

## Levantar en local

```bash
cp .env.example .env      # valores de desarrollo; nunca subas .env
docker compose up -d      # db, api (:8000) y web (:5173)
```

- Página: http://localhost:5173
- API: http://localhost:8000/api/health (responde 200 si la base contesta y 503 si no)
- Documentación interactiva de la API: http://localhost:8000/docs

Los cambios en `api/app/` y `web/` se recargan solos. Las migraciones de la base se aplican solas en cada `docker compose up`, con el servicio `migrate`, antes de que arranque la API. Para apagar todo: `docker compose down` (agrega `-v` para borrar también la base local).

Si cambias las dependencias (`api/pyproject.toml` o `web/package.json`), reconstruye con `docker compose up -d --build`.

## API: tests y lint

Los tests van contra el Postgres del compose, sin mocks (objetos simulados) de la base, así que la `db` tiene que estar arriba. Como aplican migraciones, corren en el servicio `migrate`, el único con la clave del dueño de las tablas:

```bash
docker compose run --rm migrate pytest -q --cov=app --cov-fail-under=80
docker compose run --rm migrate sh -c "ruff check . && ruff format --check . && mypy app"
```

O desde tu máquina, con Python 3.14 (toma `DATABASE_URL` y `MIGRATION_DATABASE_URL` del `.env` de la raíz):

```bash
cd api
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q --cov=app --cov-fail-under=80
ruff check . && ruff format --check . && mypy app
```

## Web: tests, lint y E2E

Desde `web/`, con Node 24:

```bash
npm ci
npm run test -- --run          # Vitest (pruebas unitarias)
npm run test:coverage          # con el mínimo de 60 % de líneas
npm run lint && npm run typecheck && npm run format:check
npx playwright install chromium   # solo la primera vez
npm run e2e                    # Playwright, con el compose arriba
```

El E2E (prueba de punta a punta) revisa además las cabeceras de seguridad y que la consola no muestre errores (ahí aparece cualquier cosa que bloquee la CSP). Para probar el build con la CSP (política de seguridad de contenido), como en producción:

```bash
npm run build && npx vite preview &
E2E_BASE_URL=http://localhost:4173 npm run e2e
```

El E2E abre la página en Chromium y espera que el estado de la API diga "ok", así que prueba el camino completo: página, proxy, API y base. Si no hay nada en el puerto 5173, levanta `npm run dev` por su cuenta, pero igual necesita la API y la base del compose.

## Base de datos: dos usuarios

La API no se conecta como dueña de las tablas. Hay dos usuarios de Postgres:

| Usuario | Variable | Puede | Lo usa |
|---|---|---|---|
| Dueño (`POSTGRES_USER`) | `MIGRATION_DATABASE_URL` | Crear, cambiar y borrar tablas | Solo el servicio `migrate` (Alembic y los tests) |
| API (`APP_DB_USER`) | `DATABASE_URL` | Leer, insertar, actualizar y borrar filas | La API |

Así, un error o una inyección de SQL en la API no puede borrar ni cambiar tablas. El usuario de la API lo crea `db/init/01-usuario-api.sh` la primera vez que arranca la base. Si tu base local es anterior a ese script, recréala con `docker compose down -v && docker compose up -d` (borra los datos locales). Los tests de `tests/test_permisos_db.py` comprueban estos límites.

## Formulario de contacto

`POST /api/contact` recibe `name`, `email`, `message`, `lang` (`es` o `en`) y, si vienen, `utm_source` y `utm_campaign`. Guarda el mensaje y responde 201; después, en segundo plano, avisa por correo con SMTP (`app/services/mail.py`, ADR 0005) y marca `emailed`. Si el correo falla o no está configurado, el mensaje igual queda guardado y el log lo anota, solo con el id del mensaje.

Contra el spam y los abusos:

- **Validación:** largos máximos iguales a los de la tabla (200, 320 y 5.000 caracteres), correo con formato válido, sin caracteres de control ni saltos de línea fuera del mensaje (así nadie puede inyectar cabeceras en el correo) y sin campos extra. Responde 422 si algo no calza.
- **Honeypot (campo trampa):** el formulario debe incluir un campo `website` oculto. Si llega con algo, es un bot: la API responde 201 igual, pero no guarda nada.
- **Límite por IP:** 5 mensajes por hora; después responde 429 con `Retry-After`. Vive en memoria del proceso, así que la API corre con un solo proceso de Uvicorn. En producción, `TRUSTED_PROXIES` tiene que incluir a Caddy para que el límite vea la IP real y no la del proxy.
- **Tamaño:** la API rechaza cuerpos de más de 64 KB (413) y los que no declaran su largo (411).
- **Al mostrarlo:** la API guarda el texto tal cual y nunca lo interpreta. El correo va en texto plano y la web lo muestra como texto (React lo escapa); nunca con `dangerouslySetInnerHTML`.

## Login del administrador

El panel tiene un solo usuario (ADR 0004), sin tabla: sus credenciales van en el `.env`.

1. Genera el hash de la contraseña (mínimo 12 caracteres): `docker compose run --rm api python -m app.hash_password`. Copia la línea `ADMIN_PASSWORD_HASH='...'` al `.env` tal cual, con las comillas simples.
2. Completa `ADMIN_EMAIL` y `JWT_SECRET` (al menos 32 caracteres al azar: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`).
3. Reinicia la API: `docker compose up -d api`.

| Ruta | Qué hace |
|---|---|
| `POST /api/admin/login` | Recibe `email` y `password`. Si calzan, deja la cookie `admin_session` y responde 200; si no, 401. Sin configuración, 503. |
| `POST /api/admin/logout` | Borra la cookie (204). |
| `GET /api/admin/session` | 200 con sesión, 401 sin ella. |

Toda ruta nueva de `/api/admin/*` va en `router` de `app/routers/admin.py`, que exige sesión por defecto; solo el login y el logout van en `public_router`. Un test recorre todas las rutas de `/api/admin/*` y falla si alguna responde sin sesión.

- **Contraseña:** hash Argon2 (`argon2-cffi`). La contraseña se verifica aunque el correo esté mal, para que el tiempo de respuesta no diga cuál falló.
- **Sesión:** JWT (JSON Web Token) firmado con HS256 y `JWT_SECRET`, de 7 días, en una cookie `httpOnly`, `Secure`, `SameSite=Strict` y con `path=/api/admin`. Cambiar `JWT_SECRET` cierra todas las sesiones; cambiar `ADMIN_EMAIL` también.
- **Límite:** 5 intentos fallidos cada 15 minutos por IP; después responde 429 con `Retry-After`. Un login correcto borra los intentos de esa IP. Usa el mismo límite en memoria y `TRUSTED_PROXIES` que el formulario de contacto.

## Contenido desde el panel

Rutas para editar lo que muestra la página. Todas exigen la sesión del administrador (sin ella, 401 antes de mirar el cuerpo) y usan JSON. Los cambios se ven en la siguiente carga de `GET /api/bootstrap`.

| Recurso | Rutas |
|---|---|
| Proyectos | `GET` y `POST /api/admin/projects`; `GET`, `PUT` y `DELETE /api/admin/projects/{id}` |
| Perfil | `GET` y `PUT /api/admin/profile` (el primer `PUT` lo crea; antes, `GET` responde 404) |
| Habilidades | `GET` y `POST /api/admin/skills`; `PUT` y `DELETE /api/admin/skills/{id}` |
| Experiencia | `GET` y `POST /api/admin/experience`; `PUT` y `DELETE /api/admin/experience/{id}` |

- **Orden y visibilidad:** cada elemento tiene `position` (el menor va primero). Un proyecto nuevo queda oculto (`visible: false`) hasta que se publica con un `PUT`. El panel ve también los ocultos.
- **`PUT` reemplaza todo:** manda el objeto completo; lo que no llega toma su valor por defecto.
- **Validación:** campos de más (como `id`), caracteres de control, largos sobre el máximo y enlaces que no sean `https://` responden 422. Un slug repetido responde 409 y un id que no existe, 404.
- **Al borrar un proyecto** se borran sus capturas en la base. Los archivos en `/media` los maneja la tarea 2.5.

## Migraciones de la API

Migraciones con Alembic (herramienta de migraciones de SQLAlchemy):

```bash
alembic revision --autogenerate -m "agrega tabla x"   # después de cambiar app/models/
alembic upgrade head                                   # aplicar
```

## Estructura

```
api/          FastAPI: app/ (routers/, models/, schemas/, services/), tests/ y alembic/ (migraciones)
db/init/      scripts que corren al crear la base (usuario de la API)
web/          React: src/ (components/, i18n/), tests/ (Vitest) y e2e/ (Playwright)
deploy/       archivos de producción (tareas 1.6, 5.3 y 5.4)
compose.yml   desarrollo local
docs/         brief, arquitectura, ADR (registros de decisión), plan y prompts; CLAUDE.md los indexa
.github/      plantilla de PR (pull request) y workflows (ci.yml, ai-review.yml)
```

## Cómo se trabaja

- Se parte desde `dev`, en una rama `feature/<nombre>`, `fix/<nombre>`, `docs/<nombre>` o `chore/<nombre>`.
- Commits con Conventional Commits en español, por ejemplo `feat: agrega formulario de contacto`.
- Un PR por tarea hacia `dev`, con la plantilla del repo. Se mergea solo con rebase & merge.
- Nunca se suben secretos ni `.env`: solo `.env.example`.

## Revisión automática con IA

El workflow `.github/workflows/ai-review.yml` revisa con Claude cada PR hacia `dev` al abrirlo o al marcarlo listo para revisión (ADR 0007). Deja como máximo unos 10 comentarios ordenados por severidad, nunca aprueba y no bloquea el merge. Se salta los borradores, los de Dependabot y los PR que solo cambian documentación (`docs/**` o `*.md`). Para pedir otra revisión, comenta `@claude revisa` en el PR.

Necesita el secreto `CLAUDE_CODE_OAUTH_TOKEN` en el repositorio (se genera con `claude setup-token`) y la app de Claude para GitHub instalada en él. Tiene permisos mínimos, acciones fijadas por SHA (hash del commit), no muestra el log completo de Claude y no corre en PR desde forks.

## Seguridad de la web

- Las cabeceras HTTP de seguridad están en `web/security-headers.ts`: `nosniff`, sin iframes, `Referrer-Policy`, `Permissions-Policy` y `Cross-Origin-Opener-Policy`. La CSP solo deja cargar scripts, estilos y datos del mismo dominio, y se aplica al build (en `npm run dev` no, porque Vite necesita un script en línea para recargar). En producción, Caddy usará estos mismos valores (tarea 1.6).
- El build no publica source maps (el código fuente original).
- El contenedor de desarrollo de la web corre con el usuario `node`, no como root.

## Primera carga y visitas: `GET /api/bootstrap`

La página llama a `GET /api/bootstrap` al abrirse. La API registra la visita, decide el idioma y devuelve todo el contenido visible en una sola respuesta, con `Cache-Control: no-store`.

Parámetros (todos opcionales; el frontend los pasa en la tarea 3.5):

| Parámetro | Qué es | Cómo se guarda |
|---|---|---|
| `utm_source`, `utm_medium`, `utm_campaign`, `utm_content` | UTM (parámetros de origen del enlace) | Sin caracteres de control ni invisibles y recortados a 200 caracteres. Nunca hacen fallar la página. |
| `referrer` | `document.referrer` de la página | Solo el dominio (`https://www.linkedin.com`); la URL completa puede traer datos personales. |
| `lang` | Idioma elegido en el selector | Manda sobre el navegador. Si no es `es` ni `en`, se ignora. |

Respuesta:

```json
{
  "lang": "es",
  "profile": {"headline_es": "", "headline_en": "", "about_es": "", "about_en": "", "links": {"github": "https://…"}},
  "skills": [{"name": "Python", "category": "language"}],
  "experience": [{"company": "", "role_es": "", "role_en": "", "description_es": "", "description_en": "", "start_date": "2024-01-01", "end_date": null}],
  "projects": [{"slug": "", "title_es": "", "title_en": "", "summary_es": "", "summary_en": "", "body_es": "", "body_en": "", "stack": [], "demo_url": null, "repo_url": null, "images": [{"url": "/media/…", "alt_es": "", "alt_en": ""}]}]
}
```

- **Idioma** (`app/services/locale.py`, ADR 0002): el primero de `Accept-Language`, que el navegador pone como preferido. Español si es `es`; si no, o si no viene el header, inglés.
- **Contenido**: textos en los dos idiomas, para que el selector cambie sin otra llamada. `profile` es `null` mientras no se cargue el perfil. Solo salen los proyectos con `visible = true`. No salen ids, orden, visibilidad, fechas de edición ni el correo de contacto.
- **Visitante único por día**: no se guarda la IP. Se guarda un HMAC-SHA256 (hash con clave) de IP y user agent, cuya clave es una sal al azar que se crea cada día (UTC) en la tabla `visitor_salt` y se borra al día siguiente. Sin la sal, ni con un respaldo de la base se puede volver a la IP.
- Si falla el registro de la visita, la página igual carga.

En producción la API está detrás de Caddy: `TRUSTED_PROXIES` tiene que incluir la red interna de Docker donde está Caddy, para que la API lea la IP real de `X-Forwarded-For`. Sin eso, todos los visitantes comparten la IP de Caddy y el conteo de únicos baja.

## CI (integración continua) y pre-commit

El workflow `.github/workflows/ci.yml` corre en cada PR y en cada push a `dev` y `main`, con cuatro jobs en paralelo:

| Job | Qué revisa |
|---|---|
| pre-commit | `ruff` (lint, formato y reglas de seguridad de Bandit), Prettier y que no se suba una llave privada |
| API | `mypy` y `pytest` contra el Postgres del compose, con cobertura mínima del 80 % |
| Web | ESLint, `tsc`, Vitest con cobertura mínima del 60 % y `vite build` |
| E2E | Playwright contra `npm run dev`, con la base, las migraciones y la API del compose |

Usa caché de pip, npm y pre-commit. No usa secretos y el token solo puede leer el código, así que corre igual de seguro en PR desde forks. Las acciones están fijadas por SHA. Un push nuevo al mismo PR cancela la corrida anterior.

Los mismos hooks de pre-commit corren en tu máquina antes de cada commit:

```bash
pip install "pre-commit==4.6.*"
pre-commit install              # una vez por clon
pre-commit run --all-files      # a mano, sobre todo el repo
```

## Seguridad en CI

El workflow `.github/workflows/security.yml` corre en cada PR, en cada push a `dev` y `main`, y los lunes a las 09:00 UTC (ADR 0007):

| Job | Qué revisa | Falla si |
|---|---|---|
| CodeQL | Análisis estático de GitHub sobre Python, TypeScript y los propios workflows | Hay un hallazgo de severidad alta o crítica (umbral del repo) |
| pip-audit | Las dependencias de la API, incluidas las de desarrollo | Hay cualquier vulnerabilidad conocida (pip-audit no filtra por severidad) |
| npm audit | Las dependencias de web, según `package-lock.json` | Hay una vulnerabilidad alta o crítica |
| Trivy | Las imágenes Docker construidas (hoy las de desarrollo; las de producción desde la tarea 1.6), salvo las librerías que pip y npm traen copiadas dentro de sí mismos | Hay una vulnerabilidad alta o crítica que ya tiene corrección |

Las reglas de seguridad de `ruff` (`S`, las de Bandit) corren en el job pre-commit de `ci.yml`. En los tests se permiten `assert` y claves de mentira; en `app/` no se usa `assert`, porque Python lo omite al correr con `-O`.

`.github/dependabot.yml` revisa cada semana pip, npm, las imágenes base y las acciones. Las versiones menores y de parche llegan en un PR por ecosistema y las mayores en uno aparte cada una. Espera 7 días desde que sale una versión antes de proponerla (por si era maliciosa y la retiran); las alertas de seguridad no esperan. Esos PR pasan por los mismos checks.

Secret scanning y push protection (que bloquea un push con un secreto) son ajustes del repo en Settings > Code security, no de un workflow.

Para correr las auditorías en tu máquina:

```bash
cd api && pip install "pip-audit==2.10.*" && pip-audit --skip-editable
cd web && npm audit --audit-level=high
```
