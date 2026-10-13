# 0008 · Environments: staging before production

Status: accepted · Date: 2026-10-11 · Requested by: Nicolas

## Context

Nicolas asked for a staging environment to test in before moving to production. It must mirror `main` and be usable to run production tests. He also asked to evaluate two environments, `staging-dev` and `staging-main`, to reduce errors both in production and in `dev`.

Today the production VPS (virtual private server) has 1 GiB of memory. Postgres, the API (application programming interface) and Caddy run there, and there is no room for a second copy of the site.

With rebase & merge (ADR 0007, architecture decision record), what is in `dev` when the release PR (pull request) is opened is exactly what will end up in `main`. That is why a permanent `staging-dev` and `staging-main` would almost always show the same code.

## Options considered

| Option | What it is | Extra monthly cost | Extra work | Cons |
|---|---|---|---|---|
| **A. Ephemeral staging per PR and permanent staging** | `staging-dev`: the whole site started on the CI (continuous integration) runner on every PR to `dev`, and torn down when done. `staging-main`: a separate VPS that mirrors production and is deployed on every merge to `dev`. | US$6 (DigitalOcean 1 GiB, no backup) | ~5 h | `staging-dev` has no URL (web address) to look at by hand; it only runs automated tests |
| B. Two permanent staging environments | A 2 GiB VPS with `staging-dev` (every merge to `dev`) and `staging-main` (every release PR), on separate subdomains | US$12 | ~7 h | They almost always show the same code, because of rebase & merge |
| C. Staging on the same production VPS | Production is upgraded to 2 GiB and staging runs alongside it | US$7.20 (from US$7.20 to US$14.40) | ~4 h | A heavy test on staging can take production down |

DigitalOcean prices checked on 2026-10-11: US$6 for 1 GiB and US$12 for 2 GiB per month.

## Decision

**A: ephemeral staging per PR and permanent staging on a separate VPS** (Nicolas, 2026-10-11). It covers the two levels he asked for at US$6 a month, isolates production, and the same staging VPS serves the upcoming products.

This applies with any option:

- **Mirroring `main`:** staging uses the same `compose.prod.yml`, the same images by SHA, the same deployment script (backup, migrations and health check) and the same Postgres version as production.
- **Data:** test seed data plus a copy of production's public content (profile, experience and projects). Contact messages and visits are never copied, because they contain personal data.
- **Its own secrets:** staging's email isn't sent to anyone; it is written to the log.
- **Access:** it is published at `staging.<domain>` with a username and password in Caddy, and with `noindex` so Google doesn't index it.
- **Gate to production:** the `dev` → `main` release PR can only be merged if staging is deployed with the same SHA and its E2E (end-to-end) tests passed. Staging's E2E tests cover the same routes that will be tested in production.
- **Workflows:** `deploy.yml` takes the environment (`staging` or `production`) as a parameter. Each GitHub environment has its own SSH (encrypted remote access) secrets.

## Consequences

- Before reaching production, every change is tested twice: on the runner, with every PR, and on staging, with every merge to `dev`.
- The fixed cost goes up from ~US$7.20 to ~US$13.20 a month with option A.
- The brief's estimate goes up to ~92 h, adding this ADR and 0007. The target date moves from 2026-10-25 to ~2026-10-27; the pessimistic scenario is still 2026-10-30.
- Migrations are tested against a database shaped like production before they are applied in production.
