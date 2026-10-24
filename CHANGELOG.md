# Changelog

Every pull request merged into `dev` is listed here, newest first. New changes go under `[Unreleased]`, and they get a version number only when a release is cut. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The [guide](#guide-how-to-read-and-update-this-file) at the end explains how the version numbers work and how to add an entry.

## [Unreleased]

### Added

- Dark theme: the public page and the admin panel follow the device's light or dark setting, with the same WCAG AA contrast as the light theme.
- Backups: `deploy/backup.sh` encrypts the daily database dump and `/media` with age and uploads them to a private Object Storage bucket with the VM's instance principal (ADR 0010 amended); `deploy-check` restores one on every PR.
- Deployment: every push to `main` publishes the API and web images to GHCR, and a manual `deploy` workflow runs `deploy/deploy.sh` on the server over SSH for a given SHA; `deploy.sh` backs up, migrates, waits for the health checks and rolls back to the previous version if they fail, which `deploy-check` now tests on every PR.

### Changed

- Code: comments in the web app, its tests and the E2E suite drop task numbers and acronym expansions; no behavior changes.
- Code: comments in the API, deploy scripts, compose files and workflows keep only the non-obvious reasons, and API tests use English names; no behavior changes.
- Docs: README, architecture, development rules and ADRs rewritten to describe the current system; ADR 0010 is renamed to free-tier deployment, and `deploy/README.md` lists the server requirements.
- `CLAUDE.md` becomes `AGENTS.md`, a short guide for coding agents with the stack, commands and conventions; `CLAUDE.md` only imports it.
- Security: Pillow goes from 12.3 to 13.0 and undici from 8.11.2 to 8.12.3 for new advisories, the web image applies Alpine security updates on build, and the Caddy Go `crypto/x509` advisory is accepted until 2026-11-24 while no Caddy image ships the fixed Go.
- Docs: ADR 0010 picks an Oracle Always Free VM for a free production deployment, after comparing free hosts (Oracle Always Free, Render with Neon, or a paid VPS); ADR 0001 and ADR 0008 stay as the target.
- Versioning: PRs add their entry under `[Unreleased]` and the version number is chosen only when a release is cut, so open PRs no longer renumber after every merge. Versions up to 0.20.11 were set per PR under the previous rule.
- `@tanstack/react-query` goes from 5.104.1 to 5.104.2, a patch release (Dependabot #53).
- `@tanstack/react-query` goes from 5.104.0 to 5.104.1, a patch release (Dependabot #47).
- The type check and the build use TypeScript 7, the native compiler; ESLint keeps the TypeScript 6 API until typescript-eslint supports 7 (replaces Dependabot #48).

### Removed

- Process documents (plan, brief, prompt log, milestone notes, ADR 0009, the local deployment guide and the Oracle setup guide) leave the repo; they were about how the project was run, not about the product.

## [0.20.11] - 2026-10-18

### Changed

- Docs: the plan and the prompt log show milestones 3 and 4 as done (only 4.6 is left), and ADR 0007 no longer has two items numbered 4.

## [0.20.10] - 2026-10-13

### Changed

- Test names, comments and helper docs in the web unit tests (`web/tests`) and E2E tests (`web/e2e`) are now in English; assertions on Spanish UI text and Spanish fixture data are unchanged (#37).

## [0.20.9] - 2026-10-13

### Changed

- Comments and JSDoc in the web code (`web/src`, the Dockerfiles and the Vite, Playwright and security header configs) are now in English, along with developer-facing error messages (#37).

## [0.20.8] - 2026-10-13

### Changed

- API test names, docstrings and comments are now in English; Spanish sample data stays as it is (#37).

## [0.20.7] - 2026-10-13

### Changed

- API code comments, docstrings, error messages and log messages are now in English, in the app, the Alembic setup, the Dockerfiles and `pyproject.toml` (#37).

## [0.20.6] - 2026-10-13

### Changed

- The project docs in `docs/` (API reference, architecture, brief, development rules, local deployment guide, plan and testing rules) are now in English, and the branch, commit, PR and test name conventions they state are now English (#37).

## [0.20.5] - 2026-10-13

### Changed

- Comments, step names and job names in the CI workflows, Dependabot, pre-commit, Trivy, Docker Compose, Caddy, `.env.example` and the DB init script are now in English, and the AI review now writes its reviews in English (#37).

## [0.20.4] - 2026-10-13

### Changed

- Translated the ADRs (architecture decision records) 0001 to 0009 to English, and ADR 0007 now states that branches, commits, PRs and documentation are in English (#37).

## [0.20.3] - 2026-10-13

### Changed

- Translated the main docs to English: CLAUDE.md, README, deploy README, PR template, prompt guide, template and log, and the milestone notes guide (#37).

## [0.20.2] - 2026-10-13

### Changed

- File names in Spanish are now in English: the ADRs, the docs in `docs/`, the prompt template and log, the DB permissions test, the API user init script and a migration (#37).

## [0.20.1] - 2026-10-13

### Added

- This changelog, with one version per merged PR since #1, and the versioning rule in the guide below (#35).

## [0.20.0] - 2026-10-13

### Added

- Admin panel: upload and delete project screenshots from the project form, with alt text in both languages (task 4.3, #36).

## [0.19.0] - 2026-10-13

### Added

- Admin panel: contact messages (mark as read or unread) and visits grouped by `utm_source` and `utm_campaign` (task 4.5, #34).

## [0.18.0] - 2026-10-13

### Added

- Admin panel: edit the profile, skills and experience in both languages (task 4.4, #33).

## [0.17.0] - 2026-10-13

### Added

- Admin panel: list and edit projects, with both languages side by side, order and visibility (task 4.2, #32).

## [0.16.0] - 2026-10-13

### Added

- Page title, `meta description` and `<html lang>` follow the chosen language, plus a `robots.txt` (task 3.6, #31).

### Changed

- Field and button borders have more contrast: 3.8:1, above the 3:1 that WCAG (Web Content Accessibility Guidelines) asks for (#31).

### Security

- The admin panel sends `noindex`, so search engines don't index it (#31).

## [0.15.0] - 2026-10-13

### Added

- The page passes the UTM parameters (tags that say where a link was shared) in its URL on to the visit and to the contact form (task 3.5, #30).

## [0.14.1] - 2026-10-13

### Changed

- CI (continuous integration) tests the admin panel with a real session, using a test admin with a random password on each run, plus an E2E (end-to-end) login test (#29).

## [0.14.0] - 2026-10-13

### Added

- `/admin` route with login, logout and route protection (task 4.1, #28).

## [0.13.0] - 2026-10-13

### Added

- Contact form on the page, with validation and messages in both languages (task 3.4, #27).

## [0.12.0] - 2026-10-13

### Added

- Projects show their screenshots, stack and links to the demo and the repository (task 3.3, #26).

## [0.11.2] - 2026-10-12

### Changed

- Docs: the repository is renamed to Portafolio-Page and the plan is updated (task 1.9, #25).

## [0.11.1] - 2026-10-12

### Added

- Docs: development and testing rules, a map of the repository, `docs/api.md` and an 80 % minimum test coverage (#24).

## [0.11.0] - 2026-10-12

### Added

- Production images, a production compose file and a check of the full deployment on every PR (task 1.6, #23).

## [0.10.0] - 2026-10-12

### Added

- Public page with profile, projects, experience and skills (task 3.1, #22).

## [0.9.0] - 2026-10-12

### Added

- API: project screenshot upload, stored as WebP (task 2.5, #20).

## [0.8.0] - 2026-10-12

### Added

- Language switcher, with the first language picked by `GET /api/bootstrap` (task 3.2, #21).

## [0.7.5] - 2026-10-12

### Added

- Rulesets for `dev` and `main`, and `sync-dev.yml` to keep `dev` in step with `main` (task 1.7, #19).

## [0.7.4] - 2026-10-12

### Changed

- Dependabot skips odd-numbered Node versions, which have no long-term support (#18).

## [0.7.3] - 2026-10-12

### Changed

- `actions/checkout` updated from 6.1.0 to 7.0.1 (#17).

## [0.7.2] - 2026-10-12

### Fixed

- Trivy and the security scans also run on `dev` and `main`, as the AI review of #14 asked (#16).

## [0.7.1] - 2026-10-12

### Security

- CI security checks: CodeQL, pip-audit, npm audit, Trivy and Dependabot (task 1.5, #14).

## [0.7.0] - 2026-10-12

### Added

- API: CRUD (create, read, update and delete) of the site content for the admin panel (task 2.4, #13).

## [0.6.1] - 2026-10-12

### Added

- Docs: local deployment and secrets guide (#12).

## [0.6.0] - 2026-10-12

### Added

- API: admin login with Argon2 password hashing, a JWT (JSON Web Token) in a cookie and a per-IP attempt limit (#11).

## [0.5.1] - 2026-10-12

### Added

- CI with `ci.yml` and pre-commit hooks (task 1.4, #10).

## [0.5.0] - 2026-10-12

### Added

- API: contact form with a honeypot field, a per-IP limit and an email notice (#9).

## [0.4.0] - 2026-10-12

### Added

- API: `GET /api/bootstrap` records the visit with its UTM parameters and picks the language (#8).

## [0.3.2] - 2026-10-12

### Added

- Docs: `CLAUDE.md` and the site documents in `docs/` (#7).

## [0.3.1] - 2026-10-12

### Fixed

- The AI review workflow is no longer cancelled by Claude's own summary comment (#6).

## [0.3.0] - 2026-10-12

### Added

- API: base models, the first migration and a database user with minimal permissions (#5).

## [0.2.1] - 2026-10-12

### Added

- CI: automatic AI review of each PR (task 1.8, #3).

## [0.2.0] - 2026-10-12

### Added

- Web skeleton with React, TypeScript, Vitest and Playwright (#4).

## [0.1.0] - 2026-10-12

### Added

- API skeleton with a health check against the database, Alembic and pytest (#2).

## [0.0.1] - 2026-10-11

### Added

- Monorepo structure and the local Docker Compose setup (task 1.1, #1).

---

## Guide: how to read and update this file

### Versioning

Versions use the SemVer (Semantic Versioning) format, `MAJOR.MINOR.PATCH`. PRs don't pick a number: they add their entry under `## [Unreleased]`, and the number is chosen once, when a release is cut, from what that section holds:

| Part    | When it goes up                                                                                            |
| ------- | ---------------------------------------------------------------------------------------------------------- |
| `MAJOR` | It stays at `0` until version 1 of the site is published (`1.0.0`). MINOR and PATCH go back to `0`.        |
| `MINOR` | When `[Unreleased]` has at least one feature (an **Added** line from a `feat` PR). PATCH goes back to `0`. |
| `PATCH` | When `[Unreleased]` only has fixes, docs, tests, refactors or chores.                                      |

Versions up to `0.20.11` were set per PR under the previous rule (until 2026-10-18) and stay as they are.

**Example.** The last release is `0.21.0`, and three PRs are merged: `feat: dark mode`, `fix: dark mode contrast` and `docs: explain dark mode`. All three add their lines under `[Unreleased]`. Since there is a feature, the next release is `0.22.0`. If only the `fix` and the `docs` PRs had been merged, it would be `0.21.1`.

### Adding an entry

1. Each PR adds its lines under `## [Unreleased]`, at the top, right under the introduction. If the section doesn't exist, the PR creates it.
2. The lines go under one or more of these headings, each with a short line that ends with the task and the PR number:
   - **Added:** something new.
   - **Changed:** something that already existed and now works differently.
   - **Fixed:** a bug.
   - **Security:** a new protection or a fixed risk.
3. Write each line for someone using the site or the panel, not for someone reading the code.
4. If another PR is merged first, the open PR is rebased and keeps its lines under `[Unreleased]`, next to the new ones.

### Cutting a release

1. A `chore: release x.y.z` PR to `dev` renames `## [Unreleased]` to `## [x.y.z] - <date>`, with the number from the table above.
2. Then the release PR `dev` → `main` is opened (ADR 0007).
3. After the release, `main` gets a SemVer tag (`v0.21.0`), and its notes are that version's section.
