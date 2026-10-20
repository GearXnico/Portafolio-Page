# deploy/

Production and staging files. The images are `api/Dockerfile` (the API, or application programming interface) and `web/Dockerfile` (Caddy with the page build and the `Caddyfile` from this folder).

| File | Task | What it does |
|---|---|---|
| `compose.prod.yml` | 1.6 | Database, migrations, API and Caddy, without root, without capabilities, with a read-only file system, memory limits and rotating logs |
| `Caddyfile` | 1.6 | Automatic HTTPS, the page, `/media`, `/api` and the same security headers as `web/security-headers.ts` |
| `deploy.sh` | 5.3 | Backup, migrations, health check and rollback |
| `backup.sh` | 5.4 | Daily `pg_dump` |

## Try it on your machine

It is the same thing the CI (continuous integration) `deploy-check` job does on every PR (pull request):

```bash
cp .env.example deploy/.env
# In deploy/.env: SITE_ADDRESS=http://localhost (HTTP only), and ADMIN_EMAIL, ADMIN_PASSWORD_HASH
# and JWT_SECRET, which production requires (how to generate them is in .env.example).
docker compose -f deploy/compose.prod.yml --env-file deploy/.env up -d --build --wait caddy
cd web && E2E_BASE_URL=http://localhost npm run e2e
docker compose -f deploy/compose.prod.yml --env-file deploy/.env down -v   # deletes the test database
```

It uses ports 80 and 443, so don't run it alongside another web server.

## Where the secrets go

The `.env` is never committed to the repo, which is public.

- **In CI:** `deploy-check` uses the example passwords from `.env.example` and test values for the admin, because the database is destroyed at the end. It needs no GitHub secrets.
- **In staging and production (milestone 5):** each server has its own `deploy/.env`, next to `compose.prod.yml`, with `600` permissions and owned by the `deploy` user. You create it once over SSH (encrypted remote access) and it doesn't change with each deployment. It holds the variables from `.env.example` with new, random values (not the ones from your machine), plus `SITE_ADDRESS` with the domain. Staging and production don't share passwords.
- **In GitHub (milestone 5):** only what the deployment workflow needs to get into the server, as secrets of the `production` environment (ADR (architecture decision record) 0008 and 0010): `DEPLOY_SSH_KEY` (a private key used only by Actions), `DEPLOY_KNOWN_HOSTS` (the server's line from `ssh-keyscan`, so another host is refused), `DEPLOY_HOST` and `DEPLOY_USER`. Limit the environment to the `main` branch.

On the server, besides `deploy/`, `db/init/` has to be there too; it creates the API user the first time the database starts.

## How a deploy works (task 5.3)

1. A push to `main` runs `.github/workflows/deploy.yml`, which builds the API and web images and publishes them to GHCR (GitHub Container Registry) as `ghcr.io/gearxnico/portafolio-page/api:<sha>` and `.../web:<sha>`. The packages must be public so the server pulls them without a token; they hold no secrets.
2. **Actions > deploy > Run workflow** with the full SHA of that commit copies `compose.prod.yml`, `deploy.sh` and `db/init/` from the same commit to `~/portafolio` on the server and runs `deploy/deploy.sh <sha>`.
3. `deploy.sh` pulls the images, backs up the database, migrates, swaps the containers and waits for the health checks. If they fail, it starts the previous version again (saved in `deploy/.deployed-tag`) and the job ends in red. To roll back on purpose, run the workflow with an older SHA.

The server never builds images: with 1 GB of memory, building the page there would be slow and could run out of memory. `deploy/.env` on the server needs `IMAGE_PREFIX=ghcr.io/gearxnico/portafolio-page`.

## Decisions in this folder

- **Fixed internal network** (`172.30.0.0/24`): `TRUSTED_PROXIES` points to it, so the API only reads `X-Forwarded-For` from Caddy (ADR 0004). Caddy replaces that header with the visitor's real IP.
- **No root:** the API runs as the `app` user (uid 10001), Caddy as `caddy` (uid 10002) and Postgres as `postgres`. Caddy has the permission to open low ports removed, because Docker already lets them be opened without privileges.
- **Memory** for the 1 GiB VPS (virtual private server): database 384 MiB, API 256 MiB and Caddy 128 MiB, 768 MiB in total.
- **No access logs:** neither Uvicorn nor Caddy records each visitor's IP, because it is personal data.
- **Migrations:** the `migrate` service runs before the API changes, and it is the only one with the table owner's password.
