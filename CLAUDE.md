# CLAUDE.md · Portfolio website

Nicolas's personal portfolio: a bilingual (Spanish and English) public page with profile, experience, projects and contact, plus an admin panel to edit it. It is also a technical piece of the portfolio, so the quality of the code, the tests and the pipeline count as much as the page.

Reply to Nico in Spanish or English; both are fine. In Spanish, keep in English the technical terms the industry uses in English. When you use an acronym, add its meaning in parentheses the first time.

Documentation, code comments, commit messages, branch names and PR (pull request) text are in English. UI (user interface) text stays bilingual through `web/src/i18n/{es,en}.json`.

## Principles (Nicolas, 2026-10-12)

- **No overengineer.** Do the minimum that solves the task; no layers, abstractions or configuration "just in case".
- **Keep it simple and secure.** Between two secure options, pick the simpler one. Security is never cut, but it is solved with the most direct thing that works.

## Documents (read only what the task needs)

| Document | Purpose |
|---|---|
| `docs/api.md` | API (application programming interface) reference: routes, validations and protections |
| `docs/development.md` | Development rules: when not to add layers, where each thing goes and how it is reviewed |
| `docs/testing.md` | What is tested, what is not and at which level |
| `docs/brief.md` | MVP (minimum viable product) scope and what is left out |
| `docs/architecture.md` | Components, data model, security and CI/CD (continuous integration and continuous deployment) |
| `docs/adr/` | The why behind each decision (0001 to 0009) |
| `docs/plan.md` | Milestones and tasks, with their definition of done |
| `docs/prompts/` | Prompt template and log per task |

Don't change a decision from an ADR (architecture decision record) on your own. If the code doesn't match a document, ask first.

## Stack

- **API:** Python 3.14, FastAPI 0.143, Pydantic 2.14, SQLAlchemy 2.1, Alembic 1.20, Uvicorn 0.54 and pytest 9.
- **Web:** React 19.3, Vite 8.3, TypeScript 7.0 in strict mode, React Router 8, TanStack Query 5, Vitest 5 and Playwright 1.64.
- **Database:** Postgres 18.
- **Server:** Caddy 2.11 serves the static files and `/media`, and proxies `/api`.
- **Infrastructure:** Docker Compose and GitHub Actions, with images in GHCR (GitHub Container Registry).

## Structure

```
api/        FastAPI: app/, tests/, alembic/
web/        React: src/, tests/, e2e/
deploy/     compose.prod.yml, Caddyfile, deploy.sh, backup.sh
docs/       project documents
compose.yml local development
```

## Commands

The details are in the README. Update this section if they change.

```bash
# Everything locally
cp .env.example .env
docker compose up -d                       # db, api (:8000) and web (:5173)

# API
cd api
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"                    # install dependencies
pytest -q --maxfail=1               # tests (needs the compose db)
pytest --cov=app --cov-fail-under=80
ruff check . && ruff format --check . && mypy app   # ruff includes the security rules (S)
pip install "pip-audit==2.10.*" && pip-audit --skip-editable
alembic revision --autogenerate -m "<change>"
alembic upgrade head

# Web
cd web
npm ci
npm run test -- --run                      # Vitest
npm run test:coverage                      # 80 % minimum
npm run lint && npm run typecheck
npm audit --audit-level=high
npm run e2e                                # Playwright, with the compose up

# Production locally (same as the deploy-check job); details in deploy/README.md
cp .env.example deploy/.env                 # and fill in SITE_ADDRESS, ADMIN_* and JWT_SECRET
docker compose -f deploy/compose.prod.yml --env-file deploy/.env up -d --build --wait caddy
cd web && E2E_BASE_URL=http://localhost npm run e2e

# pre-commit: ruff, Prettier and private keys; it also runs in CI
pip install "pre-commit==4.6.*" && pre-commit install   # once
pre-commit run --all-files
```

## Working rules (ADR 0007)

**Branches**

- Start from `dev`.
- Names: `feature/<descriptive-name>`, `fix/<name>`, `docs/<name>`, `chore/<name>` or `hotfix/<name>` (the last one branches off `main`).
- Lowercase, hyphenated, 2 to 4 English words.
- Never work directly on `dev` or `main`.

**Commits**

- Conventional Commits in English: `feat: add contact form`.
- Types: `feat`, `fix`, `test`, `docs`, `refactor` and `chore`.
- Each commit does one thing and leaves the tests green, because merges use rebase & merge. Before the PR, order them with `git rebase -i`.

**PR**

- One per plan task, targeting `dev`, with the template: Before, After, How to test and the checklist.
- Ideally under ~400 lines.
- Never merge, approve or force push on `dev` or `main`. On your own branch you can use `--force-with-lease`.

**Tests**

- Every `feature/*` comes with tests.
- Every `fix/*` first brings a test that reproduces the bug.
- Minimum coverage: 80 % of lines, in the API and in web.
- API tests run against a real Postgres, with no mocks (simulated objects) of the database.
- Every `/api/admin/*` route has a test for access without a session.
- Never skip, disable or delete a test to get CI green.

**Security**

- Validate inputs with Pydantic.
- Don't store secrets, `.env` or real data in the repo; version only `.env.example`.
- Don't log personal data.
- New dependencies must pass `pip-audit` or `npm audit`.

**Migrations**

- They only add, for example new optional columns.
- Removing something takes two PRs: first stop using it, then remove it.

## Code conventions

**API**

- Routes in `app/routers/`, logic in `app/services/`, models in `app/models/` and Pydantic schemas in `app/schemas/`.
- Type hints everywhere.
- Errors with `HTTPException` and a clear message.
- The language is decided only in `app/services/locale.py`, in a function that receives the country and `Accept-Language` (ADR 0002).
- Email is sent only from `app/services/mail.py` (ADR 0005).

**Bilingual content**

- Columns use the `_es` and `_en` suffixes (ADR 0003).
- Fixed UI text lives in `web/src/i18n/{es,en}.json`. No hardcoded text inside components.

**Web**

- Functional components; server data is loaded with TanStack Query.
- One component per file, in `web/src/components/`. Pages go in `web/src/pages/`.

**General**

- Code names and documentation in English; user-facing text is bilingual.

## Token saving (ADR 0009)

**Context**

- One plan task per session. When done, use `/clear`.
- Read only the documents and files the task names. For broad code searches, use a subagent.
- Don't read `node_modules/`, `dist/`, `.venv/`, lockfiles or `/media`.
- Show only a summary of test and lint output, with the errors, not the whole log.

**Way of working**

- If the task touches more than 3 files, first propose a short plan and wait for approval.
- If a task fails twice, stop and propose splitting it in the plan, instead of retrying it.

**Model**

- Sonnet for routine work.
- If the task is about design, security or a hard bug, suggest switching to Opus.

## When each task is done

1. Run tests, lint, typecheck and `pre-commit`, and confirm everything is green.
2. Open the PR to `dev` and share the link.
3. Add at the top of `CHANGELOG.md`, in English, the section with your PR's version: `feat` bumps MINOR and the other types bump PATCH. The guide is at the end of that file.
4. Add a row to `docs/prompts/log.md` with the task, the model, the tokens from `/cost`, the sessions and the PR. Fill in "Result" and "Lessons" in the prompt file.
5. If a command or a convention changed, update this file in the same PR.

## What is not done without asking

- Changing the stack, a major version or an ADR decision.
- Adding an external service or anything that has a cost. Deployment to real servers belongs to milestone 5 of the plan.
- Touching `deploy/`, the workflows or the rulesets outside the plan tasks that name them.
