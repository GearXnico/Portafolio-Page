# Portafolio-Page

Sitio web de portafolio: una página pública bilingüe (español e inglés) con perfil, experiencia, proyectos y contacto, más un panel de administración para editarla. Viene con pruebas, CI/CD (integración y despliegue continuos) y despliegue ya resueltos. Es un monorepo con tres piezas:

- **api/**: API (interfaz de programación) en Python con FastAPI.
- **web/**: frontend en React y TypeScript que se compila a archivos estáticos con Vite.
- **db**: Postgres 18.

En producción, Caddy sirve el frontend y pasa `/api` a la API, todo con Docker Compose en un VPS (servidor virtual privado).

> Estado: en construcción. La API y la web tienen su esqueleto (la página muestra si la API y la base responden), la base tiene las tablas del contenido (perfil, habilidades, experiencia, proyectos, capturas, visitas y mensajes) y la API ya entrega el contenido con `GET /api/bootstrap`, recibe mensajes de contacto, tiene el login del administrador y deja editar el contenido desde el panel. La web tiene la ruta `/admin` con login y logout, y las pantallas para editar proyectos, perfil, habilidades y experiencia, y para ver los mensajes y las visitas por UTM (las capturas desde el panel vienen en la tarea 4.3).

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

## Mapa del repositorio

Qué hay en cada carpeta y para qué sirve. Para entender una funcionalidad, sigue el camino de un pedido: `web/src/api/` llama a una ruta de `api/app/routers/`, que usa la lógica de `api/app/services/` y las tablas de `api/app/models/`.

```
api/                    La API (interfaz de programación), en Python con FastAPI
  app/
    main.py             Arma la app: middlewares y rutas
    config.py           Lee las variables de entorno (.env)
    db.py               Conexión a Postgres
    middleware.py       Límite de tamaño de los pedidos
    hash_password.py    Comando para generar el hash de la clave del administrador
    routers/            Rutas: reciben el pedido, llaman a un servicio y responden
    services/           Lógica: login, contenido, capturas, contacto, correo, idioma, visitas y límites
    schemas/            Qué datos entran y salen de cada ruta, validados con Pydantic
    models/             Tablas de la base, con SQLAlchemy
  alembic/versions/     Migraciones: cada cambio a las tablas, en orden
  tests/                Tests con pytest contra Postgres real (uno por área: test_<área>.py)
web/                    La página, en React y TypeScript
  src/
    main.tsx, App.tsx   Arranque de la web y sus rutas (`/admin` y la página pública)
    pages/              Páginas completas: la página pública, el login y el panel
    components/         Secciones de la página, un componente por archivo
    api/                Llamadas a la API
    i18n/               Textos de la interfaz en es.json y en.json
  tests/                Tests de componentes con Vitest
  e2e/                  Pruebas de punta a punta con Playwright
  security-headers.ts   Cabeceras de seguridad (las mismas que usa Caddy)
db/init/                Script que crea el usuario de la API al crear la base
deploy/                 Producción: compose.prod.yml y Caddyfile (ver deploy/README.md)
docs/                   Documentación del proyecto (tabla de abajo)
.github/
  workflows/            ci.yml (tests), security.yml (escaneos), ai-review.yml (revisión con IA) y sync-dev.yml
  rulesets/             Protección de dev y main, para importar en GitHub
  dependabot.yml        Actualización semanal de dependencias
  pull_request_template.md
compose.yml             Desarrollo local: db, migrate, api y web
.env.example            Variables de entorno de ejemplo; el .env real nunca se sube
CLAUDE.md               Instrucciones para Claude Code
```

| Documento | Para qué leerlo |
|---|---|
| `docs/api.md` | Referencia de la API: rutas, validaciones, protecciones y usuarios de la base |
| `docs/desarrollo.md` | Reglas de desarrollo: qué se construye, cuándo no agregar capas, ramas, commits y cómo se revisa |
| `docs/testing.md` | Qué se prueba, qué no y por qué existe cada tipo de prueba |
| `docs/brief.md` | Qué problema resuelve el sitio y qué queda fuera |
| `docs/arquitectura.md` | Componentes, modelo de datos, seguridad y despliegue |
| `docs/adr/` | El porqué de cada decisión, una ADR (registro de decisión de arquitectura) por archivo |
| `docs/plan.md` | Hitos y tareas, con su criterio de terminado |
| `docs/guia-despliegue-local.md` | Cómo completar el `.env`, levantar todo en local y comprobar que funciona |
| `docs/prompts/` y `docs/notas/` | Registro de prompts por tarea y notas de cierre de cada hito |

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
npm run test:coverage          # con el mínimo de 80 % de líneas
npm run lint && npm run typecheck && npm run format:check
npx playwright install chromium   # solo la primera vez
npm run e2e                    # Playwright, con el compose arriba
```

El E2E (prueba de punta a punta) revisa además las cabeceras de seguridad y que la consola no muestre errores (ahí aparece cualquier cosa que bloquee la CSP). Para probar el build con la CSP (política de seguridad de contenido), como en producción:

```bash
npm run build && npx vite preview &
E2E_BASE_URL=http://localhost:4173 npm run e2e
```

Los E2E del panel entran con el admin de prueba que leen de `E2E_ADMIN_EMAIL` y `E2E_ADMIN_PASSWORD` (los de tu `.env`, con la clave sin hashear). Sin esas variables fallan con un aviso. En el CI, cada corrida genera una clave al azar.

El E2E abre la página en Chromium y espera que `/api/bootstrap` responda bien y se vea el título, así que prueba el camino completo: página, proxy, API y base. Si no hay nada en el puerto 5173, levanta `npm run dev` por su cuenta, pero igual necesita la API y la base del compose.

## Referencia de la API

Qué hace cada ruta (`GET /api/bootstrap`, contacto, login del administrador, contenido del panel, mensajes y visitas), qué valida, cómo se protege y los dos usuarios de la base: [`docs/api.md`](docs/api.md). Para configurar el login del administrador en el `.env`, sigue su sección "Login del administrador".

## Migraciones de la API

Migraciones con Alembic (herramienta de migraciones de SQLAlchemy):

```bash
alembic revision --autogenerate -m "agrega tabla x"   # después de cambiar app/models/
alembic upgrade head                                   # aplicar
```

## Cómo se trabaja

El detalle está en `docs/desarrollo.md` y `docs/testing.md`. En corto:

- Se parte desde `dev`, en una rama `feature/<nombre>`, `fix/<nombre>`, `docs/<nombre>` o `chore/<nombre>`.
- Commits con Conventional Commits en español, por ejemplo `feat: agrega formulario de contacto`.
- Un PR por tarea hacia `dev`, con la plantilla del repo. Se mergea solo con rebase & merge.
- Nunca se suben secretos ni `.env`: solo `.env.example`.

## Revisión automática con IA

El workflow `.github/workflows/ai-review.yml` revisa con Claude cada PR hacia `dev` al abrirlo o al marcarlo listo para revisión (ADR 0007). Deja como máximo unos 10 comentarios ordenados por severidad, nunca aprueba y no bloquea el merge. Se salta los borradores, los de Dependabot y los PR que solo cambian documentación (`docs/**` o `*.md`). Para pedir otra revisión, comenta `@claude revisa` en el PR.

Necesita el secreto `CLAUDE_CODE_OAUTH_TOKEN` en el repositorio (se genera con `claude setup-token`) y la app de Claude para GitHub instalada en él. Tiene permisos mínimos, acciones fijadas por SHA (hash del commit), no muestra el log completo de Claude y no corre en PR desde forks.

## Seguridad de la web

- Las cabeceras HTTP de seguridad están en `web/security-headers.ts`: `nosniff`, sin iframes, `Referrer-Policy`, `Permissions-Policy` y `Cross-Origin-Opener-Policy`. La CSP solo deja cargar scripts, estilos y datos del mismo dominio, y se aplica al build (en `npm run dev` no, porque Vite necesita un script en línea para recargar). En producción, `deploy/Caddyfile` pone estos mismos valores más HSTS (solo HTTPS), y el job `deploy-check` lo comprueba.
- El build no publica source maps (el código fuente original).
- El contenedor de desarrollo de la web corre con el usuario `node`, no como root. En producción ningún contenedor corre como root (ver `deploy/README.md`).

## CI (integración continua) y pre-commit

El workflow `.github/workflows/ci.yml` corre en cada PR y en cada push a `dev` y `main`, con cinco jobs en paralelo:

| Job | Qué revisa |
|---|---|
| pre-commit | `ruff` (lint, formato y reglas de seguridad de Bandit), Prettier y que no se suba una llave privada |
| API | `mypy` y `pytest` contra el Postgres del compose, con cobertura mínima del 80 % |
| Web | ESLint, `tsc`, Vitest con cobertura mínima del 80 % y `vite build` |
| E2E | Playwright contra `npm run dev`, con la base, las migraciones y la API del compose |
| Despliegue (`deploy-check`) | Levanta `deploy/compose.prod.yml` con las imágenes de producción, respalda la base con `pg_dump`, aplica las migraciones, revisa que ningún contenedor corra como root y pasa el E2E contra Caddy. Es el staging efímero de cada PR (ADR 0008) |

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
| Trivy | Las imágenes de producción (`api/Dockerfile` y `web/Dockerfile`) | Hay una vulnerabilidad alta o crítica que ya tiene corrección y no está aceptada en `.trivyignore` |

Las reglas de seguridad de `ruff` (`S`, las de Bandit) corren en el job pre-commit de `ci.yml`. En los tests se permiten `assert` y claves de mentira; en `app/` no se usa `assert`, porque Python lo omite al correr con `-O`.

`.github/dependabot.yml` revisa cada semana pip, npm, las imágenes base y las acciones. Las versiones menores y de parche llegan en un PR por ecosistema y las mayores en uno aparte cada una. Espera 7 días desde que sale una versión antes de proponerla (por si era maliciosa y la retiran); las alertas de seguridad no esperan. Esos PR pasan por los mismos checks.

`.trivyignore` lista los hallazgos aceptados, cada uno con fecha de vencimiento (`exp:`). Hoy son solo tres de Caddy 2.11.7 (denegación de servicio en HTTP/2 y TLS), que corrige la próxima versión de Caddy. Las imágenes de producción no llevan pip ni npm. Al vencer, el job vuelve a fallar y se revisan de nuevo. Cada ID se ignora en toda la imagen; si una dependencia propia cae en uno de esos mismos CVE, la detectan igual `pip-audit` y `npm audit`, que no leen ese archivo.

Secret scanning y push protection (que bloquea un push con un secreto) son ajustes del repo en Settings > Code security, no de un workflow. Ahí mismo, el "default setup" de CodeQL tiene que quedar desactivado, porque este workflow es la configuración avanzada y GitHub no acepta las dos a la vez.

Para correr las auditorías en tu máquina:

```bash
cd api && pip install "pip-audit==2.10.*" && pip-audit --skip-editable
cd web && npm audit --audit-level=high
```

## Reglas de ramas

`dev` y `main` están protegidas con tres rulesets de GitHub (ADR 0007). Su configuración exacta está en `.github/rulesets/`, para versionarla y poder volver a importarla en Settings > Rules > Rulesets > New ruleset > Import a ruleset.

| Ruleset | Rama | Reglas | Quién se lo salta |
|---|---|---|---|
| `main` | `main` | Sin borrado ni force push, historial lineal, PR obligatorio, solo rebase & merge y los 11 checks de `ci.yml` y `security.yml` en verde con la rama al día | Nadie |
| `dev` | `dev` | Las mismas | La deploy key de `sync-dev.yml` |
| `aprobacion` | `dev` y `main` | 1 aprobación; un push nuevo la descarta | El rol admin (solo Nicolas) al mergear un PR, con bypass registrado, y la deploy key |

La aprobación va en un ruleset aparte para que el bypass salte solo la aprobación y no los checks. En Settings > General, el único método de merge habilitado es rebase & merge, y está activo "Always suggest updating pull request branches" para poner la rama al día con rebase desde el PR.

Si un job cambia de nombre o se agrega uno nuevo, se actualiza su JSON y el ruleset en GitHub en el mismo PR; si no, el check queda esperando y bloquea el merge.

### `sync-dev.yml`

Después de cada push a `main` (un PR de versión o un hotfix), rebasa `dev` sobre `main` y la publica con force push. Así `dev` descarta las copias de commits que el rebase & merge dejó en `main` con otro SHA, y recibe los hotfix. Si el rebase choca, el job falla sin publicar nada y el conflicto se resuelve a mano.

Necesita una deploy key con permiso de escritura, que se crea una vez:

```bash
ssh-keygen -t ed25519 -N "" -C sync-dev -f sync-dev
```

1. Settings > Deploy keys > Add deploy key: título `sync-dev`, el contenido de `sync-dev.pub` y "Allow write access".
2. Settings > Secrets and variables > Actions > New repository secret: `SYNC_DEV_SSH_KEY`, con el contenido de `sync-dev` (la llave privada).
3. Borra los dos archivos de tu equipo.
