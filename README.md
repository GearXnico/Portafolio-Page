# plantilla-producto

Plantilla para empezar productos web con pruebas, CI/CD (integración y despliegue continuos) y despliegue ya resueltos. Es un monorepo con tres piezas:

- **api/**: API (interfaz de programación) en Python con FastAPI.
- **web/**: frontend que se compila a archivos estáticos con Vite.
- **db**: Postgres 18.

En producción, Caddy sirve el frontend y pasa `/api` a la API, todo con Docker Compose en un VPS (servidor virtual privado).

> Estado: en construcción (hito 1 del plan). Por ahora la API y la página están vacías.

## Requisitos

- Docker con Docker Compose v2.
- Git.

## Levantar en local

```bash
cp .env.example .env      # valores de desarrollo; nunca subas .env
docker compose up -d      # db, api (:8000) y web (:5173)
```

- Página: http://localhost:5173
- API: http://localhost:8000/api/health
- Documentación interactiva de la API: http://localhost:8000/docs

Los cambios en `api/app/` y `web/` se recargan solos. Para apagar todo: `docker compose down` (agrega `-v` para borrar también la base local).

Si cambias las dependencias (`api/pyproject.toml` o `web/package.json`), reconstruye con `docker compose up -d --build`.

## Estructura

```
api/          FastAPI (app/; tests/ y alembic/ llegan en la tarea 1.2)
web/          frontend (React y TypeScript llegan en la tarea 1.3)
deploy/       archivos de producción (tareas 1.6, 5.3 y 5.4)
compose.yml   desarrollo local
.github/      plantilla de PR (pull request); los workflows llegan en las tareas 1.4 a 1.8
```

## Cómo se trabaja

- Se parte desde `dev`, en una rama `feature/<nombre>`, `fix/<nombre>`, `docs/<nombre>` o `chore/<nombre>`.
- Commits con Conventional Commits en español, por ejemplo `feat: agrega formulario de contacto`.
- Un PR por tarea hacia `dev`, con la plantilla del repo. Se mergea solo con rebase & merge.
- Nunca se suben secretos ni `.env`: solo `.env.example`.
