# deploy/

The production stack. The images are built from `api/Dockerfile` and `web/Dockerfile` (Caddy with the page build and the `Caddyfile` from this folder).

| File | What it does |
|---|---|
| `compose.prod.yml` | Database, migrations, API and Caddy, without root or capabilities, with read-only file systems, memory limits and rotating logs |
| `Caddyfile` | Automatic HTTPS, the page, `/media`, `/api` and the same security headers as `web/security-headers.ts` |
| `deploy.sh` | Backup, migrations, container swap, health checks and rollback |
| `backup.sh` | Daily `pg_dump` and `/media`, encrypted with age and uploaded to a private bucket |

## Try it locally

This is what CI's `deploy-check` job does on every PR:

```bash
cp .env.example deploy/.env
# In deploy/.env: SITE_ADDRESS=http://localhost (HTTP only), plus ADMIN_EMAIL, ADMIN_PASSWORD_HASH
# and JWT_SECRET, which production requires (.env.example explains how to generate them).
docker compose -f deploy/compose.prod.yml --env-file deploy/.env up -d --build --wait caddy
DEPLOY_PULL=0 deploy/deploy.sh local      # deploy as on the server, with the local images
cd web && E2E_BASE_URL=http://localhost npm run e2e
docker compose -f deploy/compose.prod.yml --env-file deploy/.env down -v   # deletes the test database
```

It uses ports 80 and 443, so it can't run alongside another web server.

## Secrets

The repository is public, so `.env` is never committed.

- **CI:** `deploy-check` uses the example passwords from `.env.example` and test admin values, because the database is destroyed at the end. It needs no GitHub secrets.
- **Server:** `deploy/.env`, next to `compose.prod.yml`, mode `600` and owned by the `deploy` user. It is created once and doesn't change between deploys. It holds the variables from `.env.example` with new random values, plus `SITE_ADDRESS`, `IMAGE_PREFIX=ghcr.io/gearxnico/portafolio-page`, `BACKUP_AGE_RECIPIENT` and `BACKUP_BUCKET`.
- **GitHub:** only what the deploy workflow needs to reach the server, as secrets of the `production` environment, which is limited to `main`: `DEPLOY_SSH_KEY` (a key used only by Actions), `DEPLOY_KNOWN_HOSTS` (the server's `ssh-keyscan` line, so any other host is refused), `DEPLOY_HOST` and `DEPLOY_USER`.

## Server requirements

- A Linux VM with Docker and Compose v2, ports 80, 443 and 443/udp open, automatic security updates and 2 GB of swap.
- A `deploy` user in the `docker` group. That makes it equivalent to root on the VM, so its only authorized key is the workflow's, prefixed with `restrict` to turn off forwarding and terminals.
- `age` and the `oci` CLI for `backup.sh`, and this crontab for `deploy`:

  ```
  PATH=/home/deploy/.local/bin:/usr/local/bin:/usr/bin:/bin
  15 4 * * * $HOME/portafolio/deploy/backup.sh >> $HOME/backup.log 2>&1
  ```

## How a deploy works

1. A push to `main` runs `.github/workflows/deploy.yml`, which builds the API and web images and publishes them to GHCR as `ghcr.io/gearxnico/portafolio-page/api:<sha>` and `.../web:<sha>`. The packages are public so the server pulls them without a token; they hold no secrets.
2. **Actions > deploy > Run workflow** with the full SHA of that commit copies `compose.prod.yml`, `deploy.sh`, `backup.sh` and `db/init/` from the same commit to `~/portafolio` on the server and runs `deploy/deploy.sh <sha>`.
3. `deploy.sh` pulls the images, backs up the database, migrates, swaps the containers and waits for the health checks. If they fail, it starts the previous version again (recorded in `deploy/.deployed-tag`) and the job ends red. Rolling back on purpose is the same run with an older SHA.

The server never builds images: with 1 GB of memory, building the page there would be slow and could run out of memory.

## Backups and restore

`backup.sh` encrypts the database dump and `/media` with [age](https://age-encryption.org) to the public key in `BACKUP_AGE_RECIPIENT`, keeps the last 3 on the server and uploads each one to the private Object Storage bucket `BACKUP_BUCKET`. The VM uploads with its own identity (instance principal), and its policy only allows creating objects and listing their names, so a compromised server can't read, replace or delete the backups. A lifecycle rule deletes them after 14 days. The private key is kept offline; without it no backup can be read. `deploy-check` makes a backup and restores it on every PR.

To restore, with the production compose running (see "Try it locally"):

```bash
# 1. Download the file from the bucket and decrypt it.
mkdir restore && age --decrypt --identity backup-key.txt portafolio-<date>.tar.age | tar -xf - -C restore
# 2. Database: replaces its content ("app" is POSTGRES_USER and POSTGRES_DB).
docker compose -f deploy/compose.prod.yml --env-file deploy/.env exec -T db \
  pg_restore -U app -d app --clean --if-exists --no-owner < restore/db.dump
# 3. Screenshots.
docker compose -f deploy/compose.prod.yml --env-file deploy/.env exec -T api \
  tar -xf - -C /media < restore/media.tar
```

If the VM is replaced, update the bucket policy first: it is tied to the old VM's OCID. A monthly copy of the latest backup is kept outside the cloud account, and that check is also how a failing cron job shows up (a missing day, or `~/backup.log` on the server). `backup.sh` exits with an error when the bucket variable is missing or the upload fails.

`deploy.sh` also leaves an unencrypted dump in `deploy/backups/` before each deploy, readable only by `deploy` (`umask 077`). It holds the same data as the database volume on the same disk, so it adds no exposure, and it never leaves the server.

## Decisions in this folder

- **Fixed internal network** (`172.30.0.0/24`): `TRUSTED_PROXIES` points to it, so the API only reads `X-Forwarded-For` from Caddy, which replaces that header with the visitor's real IP.
- **No root:** the API runs as `app` (uid 10001), Caddy as `caddy` (uid 10002) and Postgres as `postgres`. Caddy drops the capability to bind low ports, because Docker already allows it without privileges.
- **Memory** for a 1 GiB VM: database 384 MiB, API 256 MiB and Caddy 128 MiB, 768 MiB in total.
- **No access logs:** neither Uvicorn nor Caddy records visitor IPs, because they are personal data.
- **Migrations:** the `migrate` service runs before the API is swapped, and it is the only one with the table owner's password.
