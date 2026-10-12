# plantilla-producto

Plantilla para empezar productos web con pruebas, CI/CD (integración y despliegue continuos) y despliegue ya resueltos. Es un monorepo con tres piezas:

- **api/**: API (interfaz de programación) en Python con FastAPI.
- **web/**: frontend en React y TypeScript que se compila a archivos estáticos con Vite.
- **db**: Postgres 18.

En producción, Caddy sirve el frontend y pasa `/api` a la API, todo con Docker Compose en un VPS (servidor virtual privado).

> Estado: en construcción (hito 1 del plan). La API y la web tienen su esqueleto: la página muestra si la API y la base responden.

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

Los cambios en `api/app/` y `web/` se recargan solos. Las migraciones de la base se aplican solas cada vez que arranca la API. Para apagar todo: `docker compose down` (agrega `-v` para borrar también la base local).

Si cambias las dependencias (`api/pyproject.toml` o `web/package.json`), reconstruye con `docker compose up -d --build`.

## API: tests y lint

Los tests van contra el Postgres del compose, sin mocks (objetos simulados) de la base, así que la `db` tiene que estar arriba. Puedes correrlos dentro del contenedor:

```bash
docker compose exec api pytest -q --cov=app --cov-fail-under=80
docker compose exec api sh -c "ruff check . && ruff format --check . && mypy app"
```

O desde tu máquina, con Python 3.14 (toma `DATABASE_URL` del `.env` de la raíz):

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

## Migraciones de la API

Migraciones con Alembic (herramienta de migraciones de SQLAlchemy):

```bash
alembic revision --autogenerate -m "agrega tabla x"   # después de cambiar app/models/
alembic upgrade head                                   # aplicar
```

## Estructura

```
api/          FastAPI: app/ (routers/, models/), tests/ y alembic/ (migraciones)
web/          React: src/ (components/, i18n/), tests/ (Vitest) y e2e/ (Playwright)
deploy/       archivos de producción (tareas 1.6, 5.3 y 5.4)
compose.yml   desarrollo local
.github/      plantilla de PR (pull request); los workflows llegan en las tareas 1.4 a 1.8
```

## Cómo se trabaja

- Se parte desde `dev`, en una rama `feature/<nombre>`, `fix/<nombre>`, `docs/<nombre>` o `chore/<nombre>`.
- Commits con Conventional Commits en español, por ejemplo `feat: agrega formulario de contacto`.
- Un PR por tarea hacia `dev`, con la plantilla del repo. Se mergea solo con rebase & merge.
- Nunca se suben secretos ni `.env`: solo `.env.example`.

## Seguridad de la web

- Las cabeceras HTTP de seguridad están en `web/security-headers.ts`: `nosniff`, sin iframes, `Referrer-Policy`, `Permissions-Policy` y `Cross-Origin-Opener-Policy`. La CSP solo deja cargar scripts, estilos y datos del mismo dominio, y se aplica al build (en `npm run dev` no, porque Vite necesita un script en línea para recargar). En producción, Caddy usará estos mismos valores (tarea 1.6).
- El build no publica source maps (el código fuente original).
- El contenedor de desarrollo de la web corre con el usuario `node`, no como root.
