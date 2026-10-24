# AGENTS.md

Guidance for coding agents working in this repository.

Bilingual (Spanish and English) portfolio site: a public page with profile, projects, experience and contact, plus an admin panel to edit the content.

## Principles

- Do the minimum that solves the task. No layers, abstractions or configuration "just in case".
- Between two secure options, pick the simpler one. Security is never traded away.
- Write code a reviewer can read without comments. Comment only a non-obvious *why*.

## Stack

- **API:** Python 3.14, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, pytest.
- **Web:** React 19, TypeScript (strict), Vite, React Router, TanStack Query, Vitest, Playwright.
- **Database:** Postgres 18.
- **Serving:** Caddy serves the static build and `/media`, and proxies `/api`.
- **Infrastructure:** Docker Compose, GitHub Actions, images in GHCR.

## Layout

```
api/        FastAPI app (app/), tests (tests/), migrations (alembic/)
web/        React app (src/), unit tests (tests/), Playwright tests (e2e/)
deploy/     compose.prod.yml, Caddyfile, deploy.sh, backup.sh
docs/       architecture, API reference, testing, development rules, ADRs
compose.yml local development
```

## Commands

```bash
cp .env.example .env && docker compose up -d     # db, api (:8000), web (:5173)

# API (tests need the compose db)
docker compose run --rm migrate pytest -q --cov=app --cov-fail-under=80
docker compose run --rm migrate sh -c "ruff check . && ruff format --check . && mypy app"
alembic revision --autogenerate -m "<change>"

# Web
cd web && npm ci
npm run test:coverage
npm run lint && npm run typecheck && npm run format:check
npm run e2e                                      # needs the compose up

# Production build locally (same as CI's deploy-check job)
docker compose -f deploy/compose.prod.yml --env-file deploy/.env up -d --build --wait caddy
DEPLOY_PULL=0 deploy/deploy.sh local

pre-commit run --all-files
```

## Code conventions

**API**

- Routes in `app/routers/`, logic in `app/services/`, models in `app/models/`, schemas in `app/schemas/`.
- Type hints everywhere. Validate input with Pydantic.
- Errors are `HTTPException` with a clear message.
- Language is resolved only in `app/services/locale.py`; email is sent only from `app/services/mail.py`.

**Web**

- Functional components, one per file in `src/components/`; pages in `src/pages/`.
- Server data goes through TanStack Query.
- UI text lives in `src/i18n/{es,en}.json`, never hardcoded in components.

**Content and data**

- Bilingual columns use the `_es` and `_en` suffixes.
- Migrations only add (new tables, optional columns). Removing something takes two PRs: stop using it, then drop it.

**General**

- Code, comments, docs, commits and PRs in English.
- Names in English, including tests.

## Workflow

- Branch from `dev`: `feature/`, `fix/`, `docs/`, `chore/` (or `hotfix/` from `main`), 2 to 4 lowercase words.
- Conventional Commits; each commit does one thing and keeps the tests green (merges use rebase & merge).
- One focused PR to `dev`, ideally under 400 lines, using the PR template.
- Every change records an entry under `## [Unreleased]` in `CHANGELOG.md`.
- Never push to, merge into or force-push `dev` or `main`.

## Tests

- Every feature ships with tests; every fix starts with a test that reproduces the bug.
- Minimum line coverage: 80 % in the API and in the web app.
- API tests run against a real Postgres, without database mocks.
- Every `/api/admin/*` route has a test for access without a session.
- Never skip, disable or delete a test to get CI green.

## Security

- No secrets, `.env` files or real personal data in the repo; only `.env.example`.
- Don't log personal data.
- New dependencies must pass `pip-audit` or `npm audit --audit-level=high`.

## Ask before

- Changing the stack, a major version or a decision recorded in `docs/adr/`.
- Adding an external or paid service.
- Changing `deploy/`, the workflows or the rulesets.
