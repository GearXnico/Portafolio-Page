# Portafolio-Page

Portfolio website: a bilingual (Spanish and English) public page with profile, experience, projects and contact, plus an admin panel to edit it. It comes with tests, CI/CD (continuous integration and continuous deployment) and deployment already solved. It is a monorepo with three pieces:

- **api/**: API (application programming interface) in Python with FastAPI.
- **web/**: frontend in React and TypeScript, built into static files with Vite.
- **db**: Postgres 18.

In production, Caddy serves the frontend and forwards `/api` to the API, all with Docker Compose on a VPS (virtual private server).

> Status: under construction. The API and the web have their skeleton (the page shows whether the API and the database respond), the database has the content tables (profile, skills, experience, projects, screenshots, visits and messages), and the API already serves the content with `GET /api/bootstrap`, receives contact messages, has the admin login and lets you edit the content from the panel. The web has the `/admin` route with login and logout, and the screens to edit projects, profile, skills and experience, and to see the messages and the visits by UTM (Urchin Tracking Module) parameters (screenshots from the panel come in task 4.3).

## Requirements

- Docker with Docker Compose v2.
- Git.

## Run locally

```bash
cp .env.example .env      # development values; never commit .env
docker compose up -d      # db, api (:8000) and web (:5173)
```

- Page: http://localhost:5173
- API: http://localhost:8000/api/health (returns 200 if the database answers and 503 if not)
- Interactive API documentation: http://localhost:8000/docs

Changes in `api/app/` and `web/` reload on their own. Database migrations are applied automatically on every `docker compose up`, by the `migrate` service, before the API starts. To shut everything down: `docker compose down` (add `-v` to also delete the local database).

If you change the dependencies (`api/pyproject.toml` or `web/package.json`), rebuild with `docker compose up -d --build`.

## Repository map

What is in each folder and what it is for. To understand a feature, follow the path of a request: `web/src/api/` calls a route in `api/app/routers/`, which uses the logic in `api/app/services/` and the tables in `api/app/models/`.

```
api/                    The API (application programming interface), in Python with FastAPI
  app/
    main.py             Builds the app: middlewares and routes
    config.py           Reads the environment variables (.env)
    db.py               Connection to Postgres
    middleware.py       Request size limit
    hash_password.py    Command to generate the hash of the admin password
    routers/            Routes: receive the request, call a service and respond
    services/           Logic: login, content, screenshots, contact, email, language, visits and limits
    schemas/            What data goes in and out of each route, validated with Pydantic
    models/             Database tables, with SQLAlchemy
  alembic/versions/     Migrations: each change to the tables, in order
  tests/                Tests with pytest against a real Postgres (one per area: test_<area>.py)
web/                    The page, in React and TypeScript
  src/
    main.tsx, App.tsx   Web startup and its routes (`/admin` and the public page)
    pages/              Full pages: the public page, the login and the panel
    components/         Page sections, one component per file
    api/                Calls to the API
    i18n/               UI text in es.json and en.json
  tests/                Component tests with Vitest
  e2e/                  End-to-end tests with Playwright
  security-headers.ts   Security headers (the same ones Caddy uses)
db/init/                Script that creates the API user when the database is created
deploy/                 Production: compose.prod.yml and Caddyfile (see deploy/README.md)
docs/                   Project documentation (table below)
.github/
  workflows/            ci.yml (tests), security.yml (scans), ai-review.yml (review with AI, artificial intelligence) and sync-dev.yml
  rulesets/             Protection for dev and main, to import into GitHub
  dependabot.yml        Weekly dependency updates
  pull_request_template.md
compose.yml             Local development: db, migrate, api and web
.env.example            Example environment variables; the real .env is never committed
CLAUDE.md               Instructions for Claude Code
```

| Document | Why read it |
|---|---|
| `docs/api.md` | API reference: routes, validations, protections and database users |
| `docs/development.md` | Development rules: what gets built, when not to add layers, branches, commits and how it is reviewed |
| `docs/testing.md` | What is tested, what is not and why each kind of test exists |
| `docs/brief.md` | What problem the site solves and what is left out |
| `docs/architecture.md` | Components, data model, security and deployment |
| `docs/adr/` | The why behind each decision, one ADR (architecture decision record) per file |
| `docs/plan.md` | Milestones and tasks, with their definition of done |
| `docs/local-deployment-guide.md` | How to fill in the `.env`, run everything locally and check that it works |
| `docs/prompts/` and `docs/notes/` | Prompt log per task and closing notes for each milestone |

## API: tests and lint

The tests run against the compose Postgres, with no mocks (simulated objects) of the database, so the `db` has to be up. Since they apply migrations, they run in the `migrate` service, the only one with the table owner's password:

```bash
docker compose run --rm migrate pytest -q --cov=app --cov-fail-under=80
docker compose run --rm migrate sh -c "ruff check . && ruff format --check . && mypy app"
```

Or from your machine, with Python 3.14 (it takes `DATABASE_URL` and `MIGRATION_DATABASE_URL` from the root `.env`):

```bash
cd api
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q --cov=app --cov-fail-under=80
ruff check . && ruff format --check . && mypy app
```

## Web: tests, lint and E2E

From `web/`, with Node 24:

```bash
npm ci
npm run test -- --run          # Vitest (unit tests)
npm run test:coverage          # with the 80 % line minimum
npm run lint && npm run typecheck && npm run format:check
npx playwright install chromium   # first time only
npm run e2e                    # Playwright, with the compose up
```

The E2E (end-to-end) test also checks the security headers and that the console shows no errors (anything the CSP blocks shows up there). To test the build with the CSP (Content Security Policy), as in production:

```bash
npm run build && npx vite preview &
E2E_BASE_URL=http://localhost:4173 npm run e2e
```

The panel E2E tests log in with the test admin they read from `E2E_ADMIN_EMAIL` and `E2E_ADMIN_PASSWORD` (the ones in your `.env`, with the unhashed password). Without those variables they fail with a warning. In CI, each run generates a random password.

The E2E test opens the page in Chromium and waits for `/api/bootstrap` to respond correctly and the title to show, so it tests the whole path: page, proxy, API and database. If nothing is on port 5173, it starts `npm run dev` on its own, but it still needs the API and the database from the compose.

## API reference

What each route does (`GET /api/bootstrap`, contact, admin login, panel content, messages and visits), what it validates, how it is protected and the two database users: [`docs/api.md`](docs/api.md). To configure the admin login in the `.env`, follow its admin login section.

## API migrations

Migrations with Alembic (SQLAlchemy's migration tool):

```bash
alembic revision --autogenerate -m "add table x"   # after changing app/models/
alembic upgrade head                                # apply
```

## How we work

The details are in `docs/development.md` and `docs/testing.md`. In short:

- Start from `dev`, on a `feature/<name>`, `fix/<name>`, `docs/<name>` or `chore/<name>` branch.
- Commits with Conventional Commits in English, for example `feat: add contact form`.
- One PR (pull request) per task targeting `dev`, with the repo template. It is merged only with rebase & merge.
- Each PR records its version and its change in `CHANGELOG.md`: `feat` bumps MINOR, the other types bump PATCH, and MAJOR counts the releases to `main`. The guide is at the end of that file.
- Secrets and `.env` are never committed: only `.env.example`.

## Automated AI review

The `.github/workflows/ai-review.yml` workflow reviews every PR targeting `dev` with Claude when it is opened or marked ready for review (ADR 0007). It leaves at most about 10 comments ordered by severity, never approves and doesn't block the merge. It skips drafts, Dependabot PRs and PRs that only change documentation (`docs/**` or `*.md`). To ask for another review, comment `@claude revisa` on the PR.

It needs the `CLAUDE_CODE_OAUTH_TOKEN` secret in the repository (generated with `claude setup-token`) and the Claude GitHub app installed on it. It has minimal permissions, actions pinned by SHA (commit hash), doesn't show Claude's full log and doesn't run on PRs from forks.

## Web security

- The HTTP security headers are in `web/security-headers.ts`: `nosniff`, no iframes, `Referrer-Policy`, `Permissions-Policy` and `Cross-Origin-Opener-Policy`. The CSP only allows loading scripts, styles and data from the same domain, and it applies to the build (not in `npm run dev`, because Vite needs an inline script for reloading). In production, `deploy/Caddyfile` sets these same values plus HSTS (HTTP Strict Transport Security, HTTPS only), and the `deploy-check` job verifies it.
- The build doesn't publish source maps (the original source code).
- The web development container runs as the `node` user, not as root. In production no container runs as root (see `deploy/README.md`).

## CI (continuous integration) and pre-commit

The `.github/workflows/ci.yml` workflow runs on every PR and on every push to `dev` and `main`, with five jobs in parallel:

| Job | What it checks |
|---|---|
| pre-commit | `ruff` (lint, formatting and Bandit security rules), Prettier and that no private key is committed |
| API | `mypy` and `pytest` against the compose Postgres, with 80 % minimum coverage |
| Web | ESLint, `tsc`, Vitest with 80 % minimum coverage and `vite build` |
| E2E | Playwright against `npm run dev`, with the database, the migrations and the API from the compose |
| Deployment (`deploy-check`) | Starts `deploy/compose.prod.yml` with the production images, backs up the database with `pg_dump`, applies the migrations, checks that no container runs as root and runs the E2E against Caddy. It is the ephemeral staging of each PR (ADR 0008) |

It uses pip, npm and pre-commit caching. It uses no secrets and the token can only read the code, so it runs just as safely on PRs from forks. Actions are pinned by SHA. A new push to the same PR cancels the previous run.

The same pre-commit hooks run on your machine before each commit:

```bash
pip install "pre-commit==4.6.*"
pre-commit install              # once per clone
pre-commit run --all-files      # manually, over the whole repo
```

## Security in CI

The `.github/workflows/security.yml` workflow runs on every PR, on every push to `dev` and `main`, and on Mondays at 09:00 UTC (ADR 0007):

| Job | What it checks | Fails if |
|---|---|---|
| CodeQL | GitHub static analysis over Python, TypeScript and the workflows themselves | There is a high or critical severity finding (repo threshold) |
| pip-audit | The API dependencies, including the development ones | There is any known vulnerability (pip-audit doesn't filter by severity) |
| npm audit | The web dependencies, according to `package-lock.json` | There is a high or critical vulnerability |
| Trivy | The production images (`api/Dockerfile` and `web/Dockerfile`) | There is a high or critical vulnerability that already has a fix and is not accepted in `.trivyignore` |

The `ruff` security rules (`S`, the Bandit ones) run in the pre-commit job of `ci.yml`. In tests, `assert` and fake passwords are allowed; in `app/` `assert` is not used, because Python drops it when running with `-O`.

`.github/dependabot.yml` checks pip, npm, the base images and the actions every week. Minor and patch versions arrive in one PR per ecosystem, and major ones each in a separate PR. It waits 7 days after a version is released before proposing it (in case it was malicious and gets pulled); security alerts don't wait. Those PRs go through the same checks.

`.trivyignore` lists the accepted findings, each with an expiration date (`exp:`). Today there are only three, from Caddy 2.11.7 (denial of service in HTTP/2 and TLS), fixed by the next Caddy version. The production images don't include pip or npm. When they expire, the job fails again and they are reviewed again. Each ID is ignored across the whole image; if one of our own dependencies falls into one of those same CVEs (Common Vulnerabilities and Exposures), `pip-audit` and `npm audit` still detect it, since they don't read that file.

Secret scanning and push protection (which blocks a push containing a secret) are repo settings in Settings > Code security, not a workflow. In that same place, CodeQL's "default setup" has to stay disabled, because this workflow is the advanced configuration and GitHub doesn't accept both at once.

To run the audits on your machine:

```bash
cd api && pip install "pip-audit==2.10.*" && pip-audit --skip-editable
cd web && npm audit --audit-level=high
```

## Branch rules

`dev` and `main` are protected with three GitHub rulesets (ADR 0007). Their exact configuration is in `.github/rulesets/`, so it is versioned and can be imported again in Settings > Rules > Rulesets > New ruleset > Import a ruleset.

| Ruleset | Branch | Rules | Who bypasses it |
|---|---|---|---|
| `main` | `main` | No deletion or force push, linear history, PR required, rebase & merge only and the 11 checks from `ci.yml` and `security.yml` green with the branch up to date | Nobody |
| `dev` | `dev` | The same | The `sync-dev.yml` deploy key |
| `aprobacion` (approval) | `dev` and `main` | 1 approval; a new push dismisses it | The admin role (only Nicolas) when merging a PR, with a recorded bypass, and the deploy key |

Approval lives in a separate ruleset so that the bypass skips only the approval and not the checks. In Settings > General, the only enabled merge method is rebase & merge, and "Always suggest updating pull request branches" is on, so the branch can be rebased up to date from the PR.

If a job is renamed or a new one is added, its JSON and the ruleset in GitHub are updated in the same PR; otherwise the check stays pending and blocks the merge.

### `sync-dev.yml`

After each push to `main` (a release PR or a hotfix), it rebases `dev` onto `main` and publishes it with a force push. That way `dev` drops the copies of commits that rebase & merge left on `main` with a different SHA, and it receives the hotfixes. If the rebase conflicts, the job fails without publishing anything and the conflict is resolved by hand.

It needs a deploy key with write access, created once:

```bash
ssh-keygen -t ed25519 -N "" -C sync-dev -f sync-dev
```

1. Settings > Deploy keys > Add deploy key: title `sync-dev`, the contents of `sync-dev.pub` and "Allow write access".
2. Settings > Secrets and variables > Actions > New repository secret: `SYNC_DEV_SSH_KEY`, with the contents of `sync-dev` (the private key).
3. Delete both files from your machine.
