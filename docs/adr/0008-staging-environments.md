# 0008 · Environments: staging before production

Status: accepted · Date: 2026-10-11

## Context

Changes should be tested in an environment that mirrors production before they reach it. Two levels were considered: one for every PR into `dev`, and one for what is about to be released to `main`.

The production VPS has 1 GiB of memory, with no room for a second copy of the site. With rebase & merge ([ADR 0007](0007-workflow-tests-and-security.md)), what is in `dev` when a release PR opens is exactly what lands on `main`, so two permanent staging environments would almost always run the same code.

## Options considered

| Option | What it is | Extra monthly cost | Setup | Cons |
|---|---|---|---|---|
| A. Ephemeral staging per PR plus a permanent staging server | The whole production stack started on the CI runner for every PR, and a separate VPS deployed on every merge to `dev` | US$6 | ~5 h | The ephemeral one has no URL to browse; it only runs automated tests |
| B. Two permanent staging environments | A 2 GiB VPS with `staging-dev` and `staging-main` on separate subdomains | US$12 | ~7 h | Almost always the same code |
| C. Staging on the production VPS | Production upgraded to 2 GiB, staging alongside | US$7.20 | ~4 h | A heavy test on staging can take production down |

DigitalOcean prices on 2026-10-11.

## Decision

A. It covers both levels for US$6 a month and keeps production isolated. In every case:

- **Mirroring production:** staging uses the same `compose.prod.yml`, images by SHA, deploy script and Postgres version.
- **Data:** seed data plus a copy of the public content. Contact messages and visits are never copied, because they hold personal data.
- **Own secrets:** staging's email goes to the log, not to anyone.
- **Access:** `staging.<domain>` behind basic auth in Caddy, with `noindex`.
- **Release gate:** the `dev` → `main` PR merges only when staging runs the same SHA and its E2E tests passed.

## Consequences

- Every change is tested twice before production: on the runner with each PR, and on staging after each merge to `dev`.
- Fixed cost grows from about US$7.20 to US$13.20 a month.
- Migrations run against a production-shaped database before production.
- The ephemeral staging is the `deploy-check` job in `ci.yml`. The permanent server and its release gate wait for the paid phase ([ADR 0010](0010-free-tier-deployment.md)).
