# API reference

What each API route does, what it validates and how it is protected. To run it and its tests, see the README; for the reasoning behind each decision, see `docs/adr/`.

The interactive documentation, generated from the code, is at http://localhost:8000/docs with the compose stack up.

## First load and visits: `GET /api/bootstrap`

The page calls `GET /api/bootstrap` when it opens. The API records the visit, decides the language and returns all the visible content in a single response, with `Cache-Control: no-store`.

Parameters (all optional). The page passes the UTM parameters in its URL, `document.referrer` and the saved language; it passes `utm_source` and `utm_campaign` to the contact form (`web/src/utm.ts`):

| Parameter | What it is | How it is stored |
|---|---|---|
| `utm_source`, `utm_medium`, `utm_campaign`, `utm_content` | UTM (Urchin Tracking Module: link source parameters) | Without control or invisible characters, and trimmed to 200 characters. They never make the page fail. |
| `referrer` | The page's `document.referrer` | Only the domain (`https://www.linkedin.com`); the full URL can carry personal data. |
| `lang` | Language chosen in the selector | Takes precedence over the browser. If it is neither `es` nor `en`, it is ignored. |

Response:

```json
{
  "lang": "es",
  "profile": {"headline_es": "", "headline_en": "", "about_es": "", "about_en": "", "links": {"github": "https://…"}},
  "skills": [{"name": "Python", "category": "language"}],
  "experience": [{"company": "", "role_es": "", "role_en": "", "description_es": "", "description_en": "", "start_date": "2024-01-01", "end_date": null}],
  "projects": [{"slug": "", "title_es": "", "title_en": "", "summary_es": "", "summary_en": "", "body_es": "", "body_en": "", "stack": [], "demo_url": null, "repo_url": null, "images": [{"url": "/media/…", "alt_es": "", "alt_en": ""}]}]
}
```

- **Language** (`app/services/locale.py`, ADR 0002): the first one in `Accept-Language`, which the browser sets as preferred. Spanish if it is `es`; otherwise, or if the header is missing, English.
- **Content**: texts in both languages, so the selector switches without another call. `profile` is `null` until the profile is loaded. Only projects with `visible = true` are returned. Ids, order, visibility, edit dates and the contact email are not returned.
- **Unique visitor per day**: the IP is not stored. What is stored is an HMAC-SHA256 (keyed hash) of the IP and user agent, whose key is a random salt created each day (UTC) in the `visitor_salt` table and deleted the next day. Without the salt, not even a database backup can lead back to the IP.
- If recording the visit fails, the page still loads.

In production the API sits behind Caddy: `deploy/compose.prod.yml` sets `TRUSTED_PROXIES` to the internal Docker network where Caddy runs, so the API reads the real IP from `X-Forwarded-For`. Without it, every visitor would share Caddy's IP and the unique count would drop.

## Contact form

`POST /api/contact` receives `name`, `email`, `message`, `lang` (`es` or `en`) and, if present, `utm_source` and `utm_campaign`. It saves the message and responds 201; then, in the background, it sends an email notice over SMTP (Simple Mail Transfer Protocol) (`app/services/mail.py`, ADR 0005) and marks `emailed`. If the email fails or is not configured, the message is still saved and the log records it, with only the message id.

Against spam and abuse:

- **Validation:** maximum lengths equal to those of the table (200, 320 and 5,000 characters), an email with a valid format, no control characters or line breaks outside the message (so nobody can inject headers into the email) and no extra fields. Responds 422 if something does not match.
- **Honeypot:** the form must include a hidden `website` field. If it arrives filled in, it is a bot: the API still responds 201 but saves nothing.
- **Per-IP limit:** 5 messages per hour; after that it responds 429 with `Retry-After`. It lives in the process memory, so the API runs with a single Uvicorn process. In production, `TRUSTED_PROXIES` must include Caddy so the limit sees the real IP and not the proxy's.
- **Size:** the API rejects bodies larger than 64 KB (413) and those that do not declare their length (411).
- **When displayed:** the API stores the text as is and never interprets it. The email is plain text and the web shows it as text (React escapes it); never with `dangerouslySetInnerHTML`.

## Administrator login

The panel has a single user (ADR 0004), with no table: its credentials go in the `.env`.

1. Generate the password hash (at least 12 characters): `docker compose run --rm api python -m app.hash_password`. Copy the `ADMIN_PASSWORD_HASH='...'` line into the `.env` as is, with the single quotes.
2. Fill in `ADMIN_EMAIL` and `JWT_SECRET` (at least 32 random characters: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`).
3. Restart the API: `docker compose up -d api`.

| Route | What it does |
|---|---|
| `POST /api/admin/login` | Receives `email` and `password`. If they match, it sets the `admin_session` cookie and responds 200; otherwise, 401. Without configuration, 503. |
| `POST /api/admin/logout` | Deletes the cookie (204). |
| `GET /api/admin/session` | 200 with a session, 401 without one. |

Every new `/api/admin/*` route goes in the `router` of `app/routers/admin.py`, which requires a session by default; only login and logout go in `public_router`. A test walks every `/api/admin/*` route and fails if any of them responds without a session.

- **Password:** Argon2 hash (`argon2-cffi`). The password is verified even if the email is wrong, so the response time does not reveal which one failed.
- **Session:** JWT signed with HS256 and `JWT_SECRET`, valid for 7 days, in an `httpOnly`, `Secure`, `SameSite=Strict` cookie with `path=/api/admin`. Changing `JWT_SECRET` closes every session; so does changing `ADMIN_EMAIL`.
- **Limit:** 5 failed attempts every 15 minutes per IP; after that it responds 429 with `Retry-After`. A successful login clears that IP's attempts. It uses the same in-memory limit and `TRUSTED_PROXIES` as the contact form.

## Content from the panel

Routes to edit what the page shows. All of them require the administrator session (without it, 401 before reading the body) and use JSON, except the screenshot upload, which is a form (multipart). Changes show up on the next `GET /api/bootstrap` load.

| Resource | Routes |
|---|---|
| Projects | `GET` and `POST /api/admin/projects`; `GET`, `PUT` and `DELETE /api/admin/projects/{id}` |
| Screenshots | `POST /api/admin/projects/{id}/images` (fields `file`, `alt_es` and `alt_en`); `DELETE /api/admin/projects/{id}/images/{image_id}` |
| Profile | `GET` and `PUT /api/admin/profile` (the first `PUT` creates it; before that, `GET` responds 404) |
| Skills | `GET` and `POST /api/admin/skills`; `PUT` and `DELETE /api/admin/skills/{id}` |
| Experience | `GET` and `POST /api/admin/experience`; `PUT` and `DELETE /api/admin/experience/{id}` |

- **Order and visibility:** each item has a `position` (the lowest goes first). A new project stays hidden (`visible: false`) until it is published with a `PUT`. The panel also sees the hidden ones.
- **`PUT` replaces everything:** send the full object; whatever is missing takes its default value.
- **Validation:** extra fields (such as `id`), control characters, lengths over the maximum and links that are not `https://` respond 422. A repeated slug responds 409 and an id that does not exist, 404.
- **Screenshots:** JPEG, PNG or WebP up to 5 MB, recognized by their content and not by the extension. The API re-encodes them as WebP (at most 2560 px per side, without metadata such as a photo's GPS or the color profile: a Display P3 screenshot will look slightly less saturated), with a random name, in `MEDIA_DIR/projects/` (`media/` by default, a Docker volume). Each project returns them in `images`, with their `url` under `/media/...`. Responds 413 if it is larger than 5 MB, 415 if it is not an accepted image and 422 if it is corrupted or exceeds 25 megapixels. Without a session, the upload responds 401 before reading the file.
- **Deleting a project or a screenshot** deletes both the rows and the files.

## Messages and visits in the panel

Routes to see what reaches the site. Like the rest of `/api/admin/*`, they require the administrator session (without it, 401 before reading the body).

| Route | What it does |
|---|---|
| `GET /api/admin/messages` | All contact messages, newest first: `id`, `created_at`, `name`, `email`, `message`, `lang`, `utm_source`, `utm_campaign` and `read`. |
| `PATCH /api/admin/messages/{id}` | Receives `{"read": true}` or `{"read": false}` and returns the message. 404 if it does not exist; 422 if `read` is not a boolean or extra fields arrive. |
| `GET /api/admin/visits` | Visits grouped by `utm_source` and `utm_campaign`, most visited first: `visits` (total) and `unique_visitors` (unique visitors per day, summed, because the hash changes every day). Visits without UTM appear in the group with both set to `null`. |

- **Personal data:** messages carry the sender's name and email; they leave only through these routes and never go to the logs. Visits are returned only as counts: no individual rows and no visitor hash.
- The `read` column already existed in `contact_message`: no migration was needed.

## Database: two users

The API does not connect as the owner of the tables. There are two Postgres users:

| User | Variable | Can | Used by |
|---|---|---|---|
| Owner (`POSTGRES_USER`) | `MIGRATION_DATABASE_URL` | Create, change and drop tables | Only the `migrate` service (Alembic and the tests) |
| API (`APP_DB_USER`) | `DATABASE_URL` | Read, insert, update and delete rows | The API |

This way, a bug or a SQL injection in the API cannot drop or change tables. The API user is created by `db/init/01-api-user.sh` the first time the database starts. If your local database predates that script, recreate it with `docker compose down -v && docker compose up -d` (this deletes local data). The tests in `tests/test_db_permissions.py` check these limits.
