# 0006 · CI/CD with GitHub Actions

Status: accepted · Date: 2026-10-11 · Decided by: Nicolas, who asked to complete these decisions during the review

## Context

The brief requires tests on every PR (pull request) and automatic deployment on every merge. Job postings ask for CI/CD (continuous integration and continuous deployment), and the pipeline must stay in the template so it can be reused. A migration or a broken release can't leave the site down until Nicolas looks at it.

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. GitHub Actions builds and publishes the images to GHCR (GitHub Container Registry) and deploys over SSH (encrypted remote access) | Free on a public repo, ~6 h | The server has to be able to pull from GHCR |
| B. GitHub Actions only tests; the server runs `git pull` and builds | ~3 h | With 1 GiB of memory, building the frontend on the server can fail; there are no versioned images to roll back to |
| C. A deployment tool on the VPS (virtual private server), such as Coolify or Kamal | ~4 h | One more piece to learn and maintain |

## Decision

A, with these rules:

- **Branches:** defined by ADR (architecture decision record) 0007 (`dev` for integration and `main` for production, with `feature/*`). `ci.yml` runs on every PR to `dev` or `main` and on every push to `dev`. Every merge to `dev` deploys to staging with the same `deploy.yml` (ADR 0008).
- **`ci.yml`:**
  - API (application programming interface): `ruff` and `pytest` against Postgres 18.
  - Web: `tsc`, ESLint, Vitest and `vite build`.
  - Builds the images without publishing them.
  - The jobs run in parallel and with caching.
- **`deploy.yml`:**
  - Runs on every push to `main`, reuses `ci.yml` and deploys only if it passes.
  - Has a manual button that takes a SHA (the commit identifier) to roll back.
  - Uses `concurrency: production` without cancelling the deployment in progress.
- **Images:** tagged by SHA and by `latest`; the server always deploys by SHA.
- **Secrets:**
  - GitHub's `production` environment holds only the SSH access.
  - The app's secrets live only in the server's `.env`.
  - The workflow has only the `contents: read` and `packages: write` permissions.
- **Deployment order:**
  1. Backup with `pg_dump`.
  2. `alembic upgrade head`.
  3. Container switch.
  4. `GET /api/health` in under 60 s. If it fails, it goes back to the previous SHA and the job turns red.
- **Migrations:** additive only; nothing is dropped in the same deployment that stops using it.
- **Dependabot:** weekly, grouped by package ecosystem.

## Consequences

- Nothing reaches production without passing the same tests as the PR, and rolling back uses the same path as deploying.
- The prior backup, together with additive-only migrations, makes it possible to go back to the previous code without restoring the database.
- Dropping a column takes two deployments: first it stops being used, and then it is removed.
- By Nicolas's decision (2026-10-11), the pipeline is first tested in CI with `deploy-check`, at no cost, and deployment to real servers happens in the last milestone of the plan.
