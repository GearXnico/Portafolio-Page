# CLAUDE.md · Sitio web de portafolio

Portafolio personal de Nicolas: una página pública bilingüe (español e inglés) con perfil, experiencia, proyectos y contacto, más un panel de administración para editarla. También es una pieza técnica del portafolio, así que la calidad del código, los tests y el pipeline cuentan tanto como la página.

Responde en español y deja en inglés los términos técnicos que se usan así en la industria. Cuando uses una sigla, agrega su significado entre paréntesis la primera vez.

## Principios (Nicolas, 2026-10-12)

- **No overengineer.** Haz lo mínimo que resuelve la tarea; nada de capas, abstracciones o configuraciones "por si acaso".
- **Keep it simple and secure.** Ante dos opciones seguras, elige la más simple. La seguridad no se recorta, pero se resuelve con lo más directo que funcione.

## Documentos (leer solo lo que la tarea necesite)

| Documento | Para qué |
|---|---|
| `docs/api.md` | Referencia de la API: rutas, validaciones y protecciones |
| `docs/development.md` | Reglas de desarrollo: cuándo no agregar capas, dónde va cada cosa y cómo se revisa |
| `docs/testing.md` | Qué se prueba, qué no y en qué nivel |
| `docs/brief.md` | Alcance del MVP (producto mínimo viable) y lo que queda fuera |
| `docs/architecture.md` | Componentes, modelo de datos, seguridad y CI/CD (integración y despliegue continuos) |
| `docs/adr/` | El porqué de cada decisión (0001 a 0009) |
| `docs/plan.md` | Hitos y tareas, con su criterio de terminado |
| `docs/prompts/` | Plantilla y registro de prompts por tarea |

No cambies una decisión de una ADR (registro de decisión de arquitectura) por tu cuenta. Si el código no calza con un documento, pregunta antes.

## Stack

- **API:** Python 3.14, FastAPI 0.143, Pydantic 2.14, SQLAlchemy 2.1, Alembic 1.20, Uvicorn 0.54 y pytest 9.
- **Web:** React 19.3, Vite 8.3, TypeScript 7.0 en modo estricto, React Router 8, TanStack Query 5, Vitest 5 y Playwright 1.64.
- **Base:** Postgres 18.
- **Servidor:** Caddy 2.11 sirve los estáticos y `/media`, y hace de proxy de `/api`.
- **Infraestructura:** Docker Compose y GitHub Actions, con imágenes en GHCR (el registro de imágenes de GitHub).

## Estructura

```
api/        FastAPI: app/, tests/, alembic/
web/        React: src/, tests/, e2e/
deploy/     compose.prod.yml, Caddyfile, deploy.sh, backup.sh
docs/       documentos del proyecto
compose.yml desarrollo local
```

## Comandos

El detalle está en el README. Actualiza esta sección si cambian.

```bash
# Todo en local
cp .env.example .env
docker compose up -d                       # db, api (:8000) y web (:5173)

# API
cd api
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"                    # instalar dependencias
pytest -q --maxfail=1               # tests (necesita la db del compose)
pytest --cov=app --cov-fail-under=80
ruff check . && ruff format --check . && mypy app   # ruff incluye las reglas de seguridad (S)
pip install "pip-audit==2.10.*" && pip-audit --skip-editable
alembic revision --autogenerate -m "<cambio>"
alembic upgrade head

# Web
cd web
npm ci
npm run test -- --run                      # Vitest
npm run test:coverage                      # mínimo 80 %
npm run lint && npm run typecheck
npm audit --audit-level=high
npm run e2e                                # Playwright, con el compose arriba

# Producción en local (lo mismo que el job deploy-check); detalle en deploy/README.md
cp .env.example deploy/.env                 # y completa SITE_ADDRESS, ADMIN_* y JWT_SECRET
docker compose -f deploy/compose.prod.yml --env-file deploy/.env up -d --build --wait caddy
cd web && E2E_BASE_URL=http://localhost npm run e2e

# pre-commit: ruff, Prettier y llaves privadas; también corre en el CI
pip install "pre-commit==4.6.*" && pre-commit install   # una vez
pre-commit run --all-files
```

## Reglas de trabajo (ADR 0007)

**Ramas**

- Se parte desde `dev`.
- Nombres: `feature/<nombre-descriptivo>`, `fix/<nombre>`, `docs/<nombre>`, `chore/<nombre>` o `hotfix/<nombre>` (este último sale de `main`).
- En minúsculas, con guiones y de 2 a 4 palabras en español.
- Nunca se trabaja directo en `dev` ni en `main`.

**Commits**

- Conventional Commits en español: `feat: agrega formulario de contacto`.
- Tipos: `feat`, `fix`, `test`, `docs`, `refactor` y `chore`.
- Cada commit hace una sola cosa y deja los tests en verde, porque se mergea con rebase & merge. Antes del PR, ordénalos con `git rebase -i`.

**PR**

- Uno por tarea del plan, hacia `dev`, con la plantilla: Antes, Después, Cómo probar y la checklist.
- Idealmente con menos de ~400 líneas.
- Nunca hagas merge, ni apruebes, ni uses force push en `dev` o `main`. En tu propia rama puedes usar `--force-with-lease`.

**Tests**

- Toda `feature/*` trae tests.
- Todo `fix/*` trae primero un test que reproduce el error.
- Cobertura mínima: 80 % de las líneas, en la API y en web.
- Los tests de la API van contra Postgres real, sin mocks (objetos simulados) de la base.
- Cada ruta de `/api/admin/*` tiene un test de acceso sin sesión.
- Nunca saltes, desactives ni borres un test para dejar el CI en verde.

**Seguridad**

- Valida las entradas con Pydantic.
- No guardes secretos, `.env` ni datos reales en el repo; versiona solo `.env.example`.
- No registres datos personales en los logs.
- Las dependencias nuevas tienen que pasar `pip-audit` o `npm audit`.

**Migraciones**

- Solo agregan, por ejemplo columnas nuevas opcionales.
- Borrar algo toma dos PR: primero se deja de usar y después se elimina.

## Convenciones de código

**API**

- Rutas en `app/routers/`, lógica en `app/services/`, modelos en `app/models/` y esquemas Pydantic en `app/schemas/`.
- Type hints en todo.
- Errores con `HTTPException` y un mensaje claro.
- El idioma se decide solo en `app/services/locale.py`, en una función que recibe el país y `Accept-Language` (ADR 0002).
- El correo se envía solo desde `app/services/mail.py` (ADR 0005).

**Contenido bilingüe**

- Las columnas van con sufijo `_es` y `_en` (ADR 0003).
- Los textos fijos de la interfaz viven en `web/src/i18n/{es,en}.json`. No hay textos en duro dentro de los componentes.

**Web**

- Componentes funcionales; los datos del servidor se cargan con TanStack Query.
- Un componente por archivo, en `web/src/components/`. Las páginas van en `web/src/pages/`.

**General**

- Nombres de código en inglés; textos para el usuario y documentación en español.

## Ahorro de tokens (ADR 0009)

**Contexto**

- Una tarea del plan por sesión. Al terminar, se usa `/clear`.
- Lee solo los documentos y archivos que la tarea nombra. Para búsquedas amplias en el código, usa un subagente.
- No leas `node_modules/`, `dist/`, `.venv/`, lockfiles ni `/media`.
- Muestra solo un resumen de la salida de tests y lint, con los errores, no todo el log.

**Forma de trabajo**

- Si la tarea toca más de 3 archivos, propón primero un plan corto y espera aprobación.
- Si una tarea falla dos veces, detente y propón dividirla en el plan, en vez de reintentarla.

**Modelo**

- Sonnet para lo rutinario.
- Si la tarea es de diseño, de seguridad o un error difícil, sugiere cambiar a Opus.

## Al terminar cada tarea

1. Corre tests, lint, typecheck y `pre-commit`, y confirma que todo está en verde.
2. Abre el PR a `dev` y entrega el enlace.
3. Agrega arriba en `CHANGELOG.md`, en inglés, la sección con la versión de tu PR: `feat` sube MINOR y los demás tipos suben PATCH. La guía está al final de ese archivo.
4. Agrega una fila en `docs/prompts/log.md` con la tarea, el modelo, los tokens de `/cost`, las sesiones y el PR. Completa "Resultado" y "Lecciones" en el archivo del prompt.
5. Si cambió un comando o una convención, actualiza este archivo en el mismo PR.

## Lo que no se hace sin preguntar

- Cambiar el stack, una versión mayor o una decisión de una ADR.
- Agregar un servicio externo o algo que tenga costo. El despliegue a servidores reales es del hito 5 del plan.
- Tocar `deploy/`, los workflows o los rulesets fuera de las tareas del plan que los nombran.
