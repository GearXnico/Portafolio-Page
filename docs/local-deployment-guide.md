# Guide: local deployment and secrets

How to fill in the `.env`, bring everything up with Docker Compose, check that it works and see the result of the CI (continuous integration) E2E (end-to-end) test without deploying anything. For the details of each piece, see the README and `docs/api.md`.

> The `.env` is never pushed to the repo (it is in `.gitignore`). The values in `.env.example` are examples: they work locally, but they are not reused on any server.

## 1. Environment variables

First copy the example:

```bash
cp .env.example .env
```

With that file as is, the page, the API (application programming interface) and the database already work. Email and the admin panel stay disabled until you fill in their variables.

### How to generate a secure value

For the passwords and the session secret, use random values:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # database passwords
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # JWT_SECRET (64 characters)
```

`token_urlsafe` only uses letters, digits, `-` and `_`. That matters for the database passwords, because they go inside a URL (`DATABASE_URL`) where `@`, `:`, `/` or `#` would break it.

### Database

| Variable | Required | What it is |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | No (`producto` by default) | Prefix for the containers and the database volume (`producto_db-data`). |
| `POSTGRES_USER` | Yes | Owner of the tables. Only the migrations (Alembic) and the tests use it, in the `migrate` service. |
| `POSTGRES_PASSWORD` | Yes | The owner's password. Generate it with `token_urlsafe(32)`. |
| `POSTGRES_DB` | Yes | Database name. |
| `APP_DB_USER` | Yes | The API user, which only reads and writes rows. It is created by `db/init/01-api-user.sh`. It must be different from `POSTGRES_USER`. |
| `APP_DB_PASSWORD` | Yes | The API user's password. Generate it with `token_urlsafe(32)`. |
| `DATABASE_URL` | Only outside Docker | URL of the API user, to run the API or pytest from your machine. Inside Docker, `compose.yml` builds it on its own. |
| `MIGRATION_DATABASE_URL` | Only outside Docker | URL of the owner, for Alembic and pytest from your machine. |

If you change database users or passwords, also update the two URLs, which repeat those values: `postgresql+psycopg://<user>:<password>@localhost:<DB_PORT>/<POSTGRES_DB>`.

**Watch out:** Postgres creates the users and their passwords only the first time, when the volume is empty. If you change any of the `POSTGRES_*` or `APP_DB_*` variables after bringing up the database, you have to recreate it (see step 3).

### Contact form email (ADR 0005)

Optional. If any of `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` or `CONTACT_NOTIFY_TO` is missing, the message is still saved and the log records that email is disabled.

| Variable | What it is |
|---|---|
| `SMTP_HOST` | SMTP (Simple Mail Transfer Protocol) server. With Gmail: `smtp.gmail.com`. |
| `SMTP_PORT` | Port. `587` by default; the API uses STARTTLS with certificate verification. |
| `SMTP_USER` | Sending account (it also goes in the sender). |
| `SMTP_PASSWORD` | With Gmail, an **app password**, never the normal password. It is created in the Google account, under Security, and requires two-step verification. |
| `CONTACT_NOTIFY_TO` | Address that receives the notice for each message. |

Locally there is no need to fill them in: the form can be tested anyway.

### Trusted proxies

| Variable | What it is |
|---|---|
| `TRUSTED_PROXIES` | IPs or networks, comma-separated, from which the API accepts `X-Forwarded-For` to learn the visitor's real IP. **Leave it empty locally.** In production, `deploy/compose.prod.yml` sets it to the internal Docker network where Caddy runs. When it is empty, nobody can fake their IP with that header. |

### Panel administrator (ADR 0004)

Optional to see the page; required to use the panel. If any is missing, `POST /api/admin/login` responds 503.

| Variable | What it is | How to generate it |
|---|---|---|
| `ADMIN_EMAIL` | Email you log in to the panel with. | You choose it. Changing it closes open sessions. |
| `ADMIN_PASSWORD_HASH` | Argon2 hash of the password; the password is never stored. | `docker compose run --rm api python -m app.hash_password` (see below). |
| `JWT_SECRET` | Signs the session cookie (JWT, JSON Web Token). | `token_urlsafe(48)`. **At least 32 characters**: if it is shorter, the API does not start. Changing it closes open sessions. |

For the hash:

```bash
docker compose run --rm api python -m app.hash_password
```

It asks for the password twice without showing it (between 12 and 256 characters) and prints a line like this:

```
ADMIN_PASSWORD_HASH='$argon2id$v=19$m=...'
```

Paste it into the `.env` **as is, with the single quotes**. The hash has several `$`, and without single quotes Docker Compose would take them as variables and cut it; login would always fail with 401.

### Ports

| Variable | Default | What it is |
|---|---|---|
| `DB_PORT` | `5432` | Postgres on your machine. If you change it, change it in the two URLs too. |
| `API_PORT` | `8000` | API. |
| `WEB_PORT` | `5173` | Page (Vite). |

Change them only if the port is already taken on your machine.

## 2. Bring everything up

Requirements: Docker with Docker Compose v2, and Git.

```bash
cp .env.example .env        # if you have not done it yet
# fill in the .env (section 1)
docker compose up -d --build
```

Compose brings up, in order:

1. `db`: Postgres 18. The first time, it runs `db/init/` and creates the API user.
2. `migrate`: applies the migrations (`alembic upgrade head`) and exits.
3. `api`: FastAPI on `:8000`, reloading when `api/app/` changes.
4. `web`: Vite on `:5173`, reloading when `web/` changes. It forwards `/api` to the API.

`--build` is only needed the first time or if you changed `api/pyproject.toml` or `web/package.json`.

## 3. After changing variables

| You changed | What to run |
|---|---|
| Email, administrator, `JWT_SECRET`, `TRUSTED_PROXIES` | `docker compose up -d`. Compose recreates the containers whose configuration changed. |
| Ports | `docker compose up -d`. |
| `POSTGRES_*` or `APP_DB_*` | `docker compose down -v && docker compose up -d`. |

`down -v` deletes the database volume, and with it **all local data**. It is needed because Postgres only creates users and passwords when it initializes an empty database: with the old database, the API would keep trying to log in with the new password and fail. Locally there is no data that matters, but never run it against a real server.

To shut down without deleting anything: `docker compose down`.

## 4. Check that it works

```bash
docker compose ps                                 # db and api "healthy" or "running"; migrate "exited (0)"
curl -i http://localhost:8000/api/health          # 200 if the API and the database respond; 503 if the database does not
```

- Open http://localhost:5173: the page shows the API status as "ok". That tests the full path: page, proxy, API and database.
- http://localhost:8000/docs has the interactive API documentation.
- If you configured the administrator, test the login (replace the email and password; do not leave it in the history of a shared server):

  ```bash
  curl -i -X POST http://localhost:8000/api/admin/login \
    -H "Content-Type: application/json" \
    -d '{"email": "your-email", "password": "your-password"}'
  ```

  200 with a `set-cookie: admin_session=...` header means it works. 401 means a wrong email or password (or the hash without single quotes), 503 means one of the three variables is missing, and 429 means the limit of 5 failed attempts in 15 minutes was exceeded.

If something fails, look at the logs: `docker compose logs api` (or `migrate`, `db`, `web`). The most common problems:

| Symptom | Likely cause |
|---|---|
| `migrate` exits with an error and the API does not start | The database has passwords different from those in the `.env`: recreate it (step 3). |
| The API crashes with a `jwt_secret` validation error | `JWT_SECRET` has fewer than 32 characters. |
| `port is already allocated` | That port is taken: change `DB_PORT`, `API_PORT` or `WEB_PORT`. |
| The page says something other than "ok" | Check `/api/health` and `docker compose logs api`. |

### Local tests

```bash
docker compose run --rm migrate pytest -q --cov=app --cov-fail-under=80   # API
cd web && npm ci && npx playwright install chromium && npm run e2e         # E2E, with the compose stack up
```

## 5. See it without deploying: the CI E2E test

You do not need to bring anything up on your machine to know whether the page works: every PR (pull request) and every push to `dev` and `main` runs the **E2E** job in `.github/workflows/ci.yml`, which brings everything up on a disposable GitHub machine.

What the job does:

1. Copies `.env.example` to `.env` (example values, no secrets; CI uses none) and brings up the database, the migrations and the API with `docker compose up -d --build --wait api`.
2. Installs Chromium and runs Playwright (`npm run e2e`), which starts `npm run dev` and opens the page in a real browser.
3. Checks three things (`web/e2e/`):
   - the page opens, shows the title and the API status says "ok" (page, proxy, API and database);
   - the response carries the security headers defined in `web/security-headers.ts`;
   - the browser console shows no errors.
4. If something fails, it prints the logs of every container in the compose stack.

Since it runs without the administrator or email configured, it does not test login or sending emails; pytest covers those in the API job.

Where to see the results:

- **On the PR:** at the end of the conversation, in the list of checks, the **ci / E2E** row turns green or red. "Details" opens the log.
- **In Actions:** the repo's **Actions** tab, the **ci** workflow, the run for the commit and the **E2E** job. The `npm run e2e` step lists each test with its result; if one fails, Playwright also leaves an annotation with the error in the run summary.
- **If it failed:** the "Compose logs on failure" step has the logs of the database, the migrations and the API. In CI, Playwright retries each failing test once; if it passes on the retry, the job stays green, but the summary counts it as flaky.

CI does not keep screenshots or videos of the page. To see it with your own eyes, bring it up locally (section 2) or wait for the staging deployment (milestone 1 of the plan).
