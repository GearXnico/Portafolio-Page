# 0001 · Deployment on a VPS with Docker Compose and Caddy

Status: accepted · Date: 2026-10-11 · Decided by: Nicolas

## Context

The site needs a frontend, an API (application programming interface) and Postgres that are always available, because a recruiter's first visit can't be slow to load. Deployment is an area Nicolas wants to strengthen, and it is also something the job postings he reviewed ask for. Besides, the server should be able to host upcoming products without multiplying the cost.

## Options considered

| Option | Monthly cost | Extra work | Cons |
|---|---|---|---|
| A. VPS (virtual private server) on DigitalOcean, 1 vCPU (virtual CPU) and 1 GiB of memory, with weekly backup | US$7.20 | ~6 h | The server has to be maintained |
| B. Render (managed API plus Postgres) | US$13 | ~1-2 h | Each new product adds the same again |
| C. Fly.io plus Neon plus static hosting | ~US$2-4 | ~4 h | The API and the database go to sleep; three providers |

Prices checked on 2026-10-11 on the official pages.

## Decision

A: a VPS on DigitalOcean (New York region) with Docker Compose. Caddy 2.11 serves the frontend, passes `/api` to FastAPI and renews the HTTPS (encrypted connection) certificate on its own. Images are built in GitHub Actions, not on the server.

## Consequences

- It is the cheapest option without slow cold starts, and the same machine hosts the upcoming products.
- Nicolas maintains the server: SSH (encrypted remote access) with keys only, firewall, automatic patches and disk alerts.
- The configuration (Compose, Caddyfile and scripts) lives in the template and is reused.
- With 1 GiB of memory, building on the server isn't possible. If a future product needs more, the plan is upgraded (US$12 for 2 GiB).
