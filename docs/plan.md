# Plan · Portfolio website

ID: 2026-10-08-sitio-portafolio · Version: draft 3 (2026-10-12) · Based on: `brief.md`, `architecture.md` and `adr/`

## Summary

This plan covers only the **portfolio site**. The repository started as `plantilla-producto`, but the code of milestones 2 and 3 is already the portfolio, so it was renamed to `Portafolio-Page` and it is finished here (Nicolas's decision, 2026-10-12). The reusable template is made later, as a separate project, by extracting what really repeats.

The overall order of work (Nicolas's decision, 2026-10-12) is this:

1. **Finish developing the portfolio:** milestones 3 and 4 of this plan.
2. **Create the template** as a new project, with its own brief and plan, from the finished portfolio.
3. **One or two quick projects** created from the template, which are then shown in the portfolio.
4. **Only then, the spending:** milestone 5 of this plan deploys the portfolio, and the other products are deployed on the same VPS (virtual private server).

Points 2 and 3 are not part of this plan: each one will have its own documents. The template is part of the ecosystem (Nicolas, 2026-10-12), so it does not take the active idea slot; the quick projects do follow the activation rules.

**Development costs nothing.** Milestones 0 to 4 use only free tools: GitHub, Actions on a public repo and Docker locally. Milestone 5 pays for the servers and the domain. Milestone 1 already built the production images and tests them in CI (continuous integration) with `deploy-check` (the ephemeral staging of ADR 0008), so milestone 5 is left with only the servers, the DNS (Domain Name System), the secrets and `deploy.yml`.

**The dates are a guide**, to see whether we are on track, not deadlines (Nicolas, 2026-10-12).

Each task is meant to be finished in one Claude Code session. It is delivered as a `feature/*`, `fix/*`, `docs/*` or `chore/*` branch with its PR (pull request) to `dev`, following ADR (architecture decision record) 0007. "Done" means the criterion in the table and that ADR's done checklist are met. Each task starts with a prompt made from `prompts/template.md` and is recorded in `prompts/log.md` (ADR 0009).

| Milestone | Deliverable | Hours | Status |
|---|---|---|---|
| 0 | Free accounts ready | 2 | Done |
| 1 | Base with CI, security and a deployment test in CI | 22.5 | Done |
| 2 | API (application programming interface) and database | 14 | Done |
| 3 | Bilingual public frontend | 17 | Done |
| 4 | Admin panel | 18 | 4.1 to 4.5 done; 4.6 pending |
| 5 | Deployment, content and release of version 1 (~US$13.20 a month plus CLP 9,990 a year for the domain) | 20.5 | After the template and the quick projects |
| | **Total** | **94** | |

Only task 4.6 remains before milestone 5 (1 h, done by Nicolas), plus the 20.5 h of milestone 5 (status on 2026-10-18).

## Milestone 0 · Free accounts (you do it, without Claude Code)

**Done on 2026-10-11:** Gmail password, `plantilla-producto` repo (public, `dev` as default, with Claude access), quotas reviewed (Actions and GHCR free on public repos) and token generated.

| # | Task | Hours | Done when |
|---|---|---|---|
| 0.1 | Create the Gmail app password (requires two-step verification) | 0.5 | You have it saved in your password manager |
| 0.2 | Create the public `plantilla-producto` repo on GitHub, empty and with `dev` as the default branch | 0.5 | The repo exists and Claude Code has access |
| 0.3 | Review with Claude Code the free quotas of GitHub Actions and GHCR (GitHub's image registry) for public repos | 0.5 | There are no cost surprises |
| 0.4 | Generate `CLAUDE_CODE_OAUTH_TOKEN` with `claude setup-token`, for the automatic review | 0.5 | You have the token saved |

## Milestone 1 · Base with CI and a deployment test, at no cost

The repo was called `plantilla-producto` because at first it was going to be the template. Task 1.9 renamed it to `Portafolio-Page`; it is no longer marked as a "template repository". The empty repo that was called `portfolio-page` became `Product-template`, for the future template.

| # | Task | Hours | Done when |
|---|---|---|---|
| 1.1 | Monorepo structure (`api/`, `web/`, `deploy/`), local `compose.yml`, README, `.env.example`, `.gitignore` and PR template | 2 | `docker compose up` brings everything up locally |
| 1.2 | API skeleton: FastAPI, `GET /api/health` that queries the database, Alembic initialized, pytest against Postgres, `ruff` and `mypy` | 3 | Tests pass locally and `/api/health` responds 200 |
| 1.3 | Web skeleton: Vite, React and strict TypeScript, ESLint, Prettier, Vitest and an E2E (end-to-end) test with Playwright that opens the page | 3 | The tests and the E2E test pass locally |
| 1.4 | `ci.yml`: API and web jobs in parallel, cache, coverage minimums (80% and 60%) and `pre-commit` | 3 | A test PR shows all checks green, and a broken test turns it red |
| 1.5 | Security in CI: CodeQL, `ruff` security rules, `pip-audit`, `npm audit`, Trivy and `dependabot.yml` | 3 | The checks run on the PR; a test vulnerable dependency blocks it |
| 1.6 | Production images: multi-stage Dockerfiles for the API and for Caddy (with the web build inside), `compose.prod.yml` (with a fixed internal network and `TRUSTED_PROXIES` pointing to it, ADR 0004), Caddyfile and a `deploy-check` job in CI, with backup and migrations as in production | 4 | `deploy-check` brings up the production compose on the runner, applies the migrations and passes the E2E test |
| 1.7 | GitHub rules: rulesets for `main` and `dev` (1 approval with your bypass, linear history, rebase & merge only, required checks) and `sync-dev.yml`. The staging gate is added in milestone 5. | 3 | A PR without green checks cannot be merged, and after a test release PR `dev` is synced |
| 1.8 | `ai-review.yml`: automatic AI (artificial intelligence) review on PRs to `dev`, with `CLAUDE_CODE_OAUTH_TOKEN` (ADR 0007) | 1 | A test PR gets comments from the reviewer and the documentation PR is skipped |
| 1.9 | Rename. **You did it (2026-10-12):** `plantilla-producto` became `Portafolio-Page` and the empty `portfolio-page` repo became `Product-template` (GitHub keeps the history, the PRs and a redirect from the old names). **With Claude Code:** update the README, `architecture.md` (section 7), the brief (point 8 and the template metric move to the template project) and this plan | 0.5 | CI runs green and no document presents this repo as the template |

**End of milestone:** every PR goes through tests, security, AI review and a test of the full deployment in CI, all at no cost, in the `Portafolio-Page` repo.

## Milestone 2 · API and database

| # | Task | Hours | Done when |
|---|---|---|---|
| 2.1 | Models and initial migration: profile, skills, experience, projects, images, visits and messages | 2 | `alembic upgrade head` creates the 7 tables, with constraint tests |
| 2.2 | `GET /api/bootstrap`: records the visit with UTM (Urchin Tracking Module: link source parameters) and a daily hash, decides the language and returns the visible content | 3 | Tests for language (es, en and no header), UTM and hidden projects |
| 2.3 | Administrator login: Argon2, JWT (JSON Web Token, a signed token) in a cookie, attempt limit and a command to generate the hash | 3 | Tests for correct login, wrong login, lockout and access without a session to `/api/admin/*` |
| 2.4 | Admin CRUD (create, read, update and delete): projects (with order and visibility), profile, skills and experience | 3 | Tests for each route, with API coverage ≥ 80% |
| 2.5 | Screenshot upload: 5 MB maximum, conversion to WebP and storage in `/media` | 1.5 | Tests with a valid image, a file that is too large and a file that is not an image |
| 2.6 | Contact: saves the message, honeypot, per-IP (network address) limit and email in a background task | 1.5 | Tests for sending, blocked spam and a failed email that still saves the message |

## Milestone 3 · Public frontend

| # | Task | Hours | Done when |
|---|---|---|---|
| 3.1 | Single-page layout: profile, skills, experience, projects and contact, responsive | 4 | It looks good on a phone and on desktop, with render tests |
| 3.2 | Languages: fixed texts in JSON, language from `bootstrap`, selector and `localStorage` | 3 | E2E: with the browser in English it shows in English, and the selector switches and is remembered |
| 3.3 | Projects section with screenshots, stack and demo and repository links | 3 | Hidden projects do not appear; component tests |
| 3.4 | Contact form with validation and success and error messages in both languages | 3 | E2E: a sent message shows up in the database |
| 3.5 | UTM: read from the URL (web address) and passed to `bootstrap` and to the contact form | 1 | E2E: a visit with UTM is recorded with its source |
| 3.6 | SEO (search engine optimization) and accessibility: titles, `meta` per language, `hreflang` and contrast | 3 | Lighthouse ≥ 90 in accessibility and SEO |

## Milestone 4 · Admin panel

| # | Task | Hours | Done when |
|---|---|---|---|
| 4.1 | `/admin` route with login, logout and route protection | 3 | E2E: without a session it redirects to the login |
| 4.2 | Project list and editing: form with both languages side by side, ordering and hiding | 5 | E2E: create a project and see it on the public page |
| 4.3 | Screenshot upload from the project form | 2 | E2E: the screenshot shows on the public page |
| 4.4 | Editing of profile, skills and experience | 4 | E2E: a profile change shows on the page |
| 4.5 | Contact messages (mark as read) and visits grouped by `utm_source` and `utm_campaign` | 3 | The messages and the counts of a test visit with UTM are visible |
| 4.6 | Test of the brief's goal: add a real project, timed | 1 | It takes less than 10 minutes |

## Milestone 5 · Deployment, content and release (spending starts here)

It starts when milestone 4 is done and tested locally and in CI, **and also** the template and at least one quick project are done (order decided by Nicolas on 2026-10-12). Before starting, review how the existing products share the VPS and Caddy.

| # | Task | Hours | Done when |
|---|---|---|---|
| 5.1 | Create the DigitalOcean account with a billing alert and your SSH (Secure Shell, encrypted remote access) key, and register the .cl domain at NIC Chile (CLP 9,990 a year). You do it. | 1 | You can create a droplet and the domain is in your name |
| 5.2 | Staging and production servers: droplets, `deploy` user, `ufw`, `unattended-upgrades`, Docker, DNS, `staging.<domain>` with user, password and `noindex` | 4 | `ssh deploy@` works on both and Caddy responds over HTTPS (encrypted connection) |
| 5.3 | `deploy.yml` and `deploy/deploy.sh` per environment: backup, migrations, container swap, health check and rollback; manual button by SHA (the commit identifier). The staging gate is turned on in the `main` ruleset. | 4.5 | A merge to `dev` deploys staging, a health check broken on purpose rolls back to the previous version on its own, and the PR to `main` requires green staging |
| 5.4 | `backup.sh` with cron, DigitalOcean weekly backup turned on and a restore test | 1 | You restored a backup on staging and the data matches |
| 5.5 | Load the profile, skills and experience in both languages, from the panel in production | 3 | The content is complete in `es` and `en` |
| 5.6 | Write the case study of the page itself: architecture, pipeline, and what the AI did and what you decided | 3 | The project is published with screenshots and a link to the repo |
| 5.7 | Final pass on staging: full E2E tests, a test on a phone and a backup restore | 2 | Everything green and no errors in the logs |
| 5.8 | Release PR to `main`, `v1.0.0` tag and UTM links for upcoming job applications | 2 | The site is public and you have 5 links ready to use |

## Plan risks

| Risk | Signal | What to do |
|---|---|---|
| The real deployment, the least practiced area, is left for the end | Tasks 5.2 or 5.3 go over 4 h each | `deploy-check` already tested the images, the compose and the migrations in milestone 1, so what remains is the server, DNS and secrets. If it gets stuck, publish production first and add staging a few days later. |
| The portfolio takes long to publish because milestone 5 waits for the template and the quick projects | Weeks go by with the portfolio finished and unpublished | A conscious decision to save costs. If a job application needs it sooner, milestone 5 can be brought forward for the portfolio only. |
| The panel grows | Milestone 4 goes over 18 h | Publish without project reordering (4.2) and without visits by UTM (4.5); add them later |
| The future template cannot update the portfolio | When the template is created | Accepted: the portfolio is not synced with the template. If it is worth it later, connect them with a one-time merge and resolve the conflicts once. |

## After version 1

- Brief metric: add more than 1 new development in the first month.
- Language detection by country with Cloudflare (ADR 0002).
- Review of the visit metrics per job application at 8 weeks.
- Add to the portfolio the quick projects made with the template, each with its case study.
