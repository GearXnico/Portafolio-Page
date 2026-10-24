# 0006 · CI/CD with GitHub Actions

Status: accepted · Date: 2026-10-11

## Context

Every PR has to be tested, and every release deployed the same way. A failed migration or a broken release must not leave the site down until someone notices.

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. Actions builds and publishes the images to GHCR and deploys over SSH | Free on a public repo, ~6 h | The server must be able to pull from GHCR |
| B. Actions only tests; the server runs `git pull` and builds | ~3 h | Building the frontend on a 1 GiB server can fail; no versioned images to roll back to |
| C. A deployment tool on the server, such as Coolify or Kamal | ~4 h | One more piece to run and maintain |

## Decision

A, with these rules:

- **`ci.yml`** runs on every PR and every push to `dev` and `main`: lint, types, unit tests, E2E and a production-like deploy on the runner (`deploy-check`). Jobs run in parallel with caching.
- **Images** are tagged by commit SHA, and the server always deploys a SHA, so the running version is always known.
- **`deploy.yml`** publishes the images on every push to `main` and deploys a given SHA over SSH. A rollback is the same run with an older SHA. Only one deployment runs at a time.
- **Deployment order:** `pg_dump`, `alembic upgrade head`, container swap, health checks. If they fail, the previous SHA starts again and the job turns red.
- **Secrets:** the `production` environment holds only the SSH access; application secrets live only in the server's `.env`. Workflow permissions are limited to `contents: read` and, for publishing, `packages: write`.
- **Migrations** only add; dropping something waits until a later release stops using it.
- **Dependabot** runs weekly, grouped by ecosystem.

## Consequences

- Nothing reaches production without the same checks as the PR, and rolling back uses the same path as deploying.
- Add-only migrations let the previous release run against the new schema, so a rollback needs no database restore; the pre-deploy dump covers data mistakes.
- Dropping a column takes two releases.
- During the free phase ([ADR 0010](0010-free-tier-deployment.md)) the deploy is started by hand with the SHA of a commit on `main`, after its images are published.
