# 0001 · Deployment on a VPS with Docker Compose and Caddy

Status: accepted · Date: 2026-10-11

## Context

The site needs a frontend, an API and Postgres that are always available: a first visit can't wait for a service to wake up. The same server should be able to host later projects without multiplying the cost.

## Options considered

| Option | Monthly cost | Setup | Cons |
|---|---|---|---|
| A. DigitalOcean VPS, 1 vCPU and 1 GiB, with weekly backup | US$7.20 | ~6 h | The server has to be maintained |
| B. Render (managed API and Postgres) | US$13 | ~1-2 h | Each new project adds the same again |
| C. Fly.io, Neon and static hosting | ~US$2-4 | ~4 h | The API and the database sleep; three providers |

Prices from the official pages on 2026-10-11.

## Decision

A: a VPS with Docker Compose. Caddy serves the frontend, proxies `/api` to FastAPI and renews the HTTPS certificate on its own. Images are built in GitHub Actions, never on the server.

## Consequences

- The cheapest option without cold starts, and the same machine can host later projects.
- The server is maintained by hand: SSH with keys only, a firewall, automatic security patches and disk alerts.
- 1 GiB is not enough to build images on the server, which is why CI builds them. A project that needs more moves to the 2 GiB plan (US$12).
- [ADR 0010](0010-free-tier-deployment.md) adds a free phase on Oracle Cloud before this target.
