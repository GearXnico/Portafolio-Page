# 0006 · CI/CD con GitHub Actions

Estado: aceptada · Fecha: 2026-10-11 · Decidió: Nicolas, que pidió completar estas decisiones en la revisión

## Contexto

El brief exige pruebas en cada PR (pull request) y despliegue automático en cada merge. Las ofertas de trabajo piden CI/CD (integración y despliegue continuos), y el pipeline debe quedar en la plantilla para reutilizarlo. Una migración o una versión rota no puede dejar el sitio caído hasta que Nicolas lo revise.

## Opciones consideradas

| Opción | Costo | Contras |
|---|---|---|
| A. GitHub Actions construye y publica las imágenes en GHCR (GitHub Container Registry) y despliega por SSH (acceso remoto cifrado) | Gratis en un repo público, ~6 h | El servidor tiene que poder descargar de GHCR |
| B. GitHub Actions solo prueba; el servidor hace `git pull` y construye | ~3 h | Con 1 GiB de memoria, construir el frontend en el servidor puede fallar; no hay imágenes versionadas para volver atrás |
| C. Herramienta de despliegue sobre el VPS (servidor virtual privado), como Coolify o Kamal | ~4 h | Una pieza más que aprender y mantener |

## Decisión

A, con estas reglas:

- **Ramas:** las define la ADR 0007 (`dev` para integración y `main` para producción, con `feature/*`). `ci.yml` corre en cada PR a `dev` o `main` y en cada push a `dev`. Cada merge a `dev` despliega a staging con el mismo `deploy.yml` (ADR 0008).
- **`ci.yml`:**
  - API: `ruff` y `pytest` contra Postgres 18.
  - Web: `tsc`, ESLint, Vitest y `vite build`.
  - Construye las imágenes sin publicarlas.
  - Los jobs corren en paralelo y con caché.
- **`deploy.yml`:**
  - Corre en cada push a `main`, reutiliza `ci.yml` y despliega solo si pasa.
  - Tiene un botón manual que recibe un SHA (identificador del commit) para volver atrás.
  - Usa `concurrency: production` sin cancelar el despliegue en curso.
- **Imágenes:** etiquetadas por SHA y por `latest`; el servidor despliega siempre por SHA.
- **Secretos:**
  - El ambiente `production` de GitHub guarda solo el acceso SSH.
  - Los secretos de la app viven solo en el `.env` del servidor.
  - El workflow tiene únicamente los permisos `contents: read` y `packages: write`.
- **Orden del despliegue:**
  1. Respaldo con `pg_dump`.
  2. `alembic upgrade head`.
  3. Cambio de contenedores.
  4. `GET /api/health` en menos de 60 s. Si falla, vuelve al SHA anterior y el job queda en rojo.
- **Migraciones:** solo agregan; nada se borra en el mismo despliegue que lo deja de usar.
- **Dependabot:** semanal, agrupado por ecosistema de paquetes.

## Consecuencias

- Nada llega a producción sin pasar las mismas pruebas que el PR, y volver atrás usa el mismo camino que desplegar.
- El respaldo previo, junto con las migraciones que solo agregan, permite volver al código anterior sin restaurar la base.
- Borrar una columna toma dos despliegues: primero se deja de usar y después se elimina.
- Por decisión de Nicolas (2026-10-11), el pipeline se prueba primero en CI con `deploy-check`, sin costo, y el despliegue a servidores reales se hace en el último hito del plan.
