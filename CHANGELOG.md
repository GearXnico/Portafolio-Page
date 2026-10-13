# Changelog

Every pull request merged into `dev` is listed here, newest first, with the version it produced. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The [guide](#guide-how-to-read-and-update-this-file) at the end explains how the version numbers work and how to add an entry.

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

Versions use the SemVer (Semantic Versioning) format, `MAJOR.MINOR.PATCH`:

| Part    | What it counts                       | When it goes up                                                                                                     |
| ------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `MAJOR` | Releases to `main`                   | When `dev` is released to `main`. It stays at `0` until the first release, `1.0.0`. MINOR and PATCH go back to `0`. |
| `MINOR` | Features merged into `dev`           | With every merged PR of type `feat`. PATCH goes back to `0`.                                                        |
| `PATCH` | Other changes since the last feature | With every other merged PR: `fix`, `docs`, `test`, `refactor` or `chore`.                                           |

Every PR merged into `dev` gets exactly one version. Its type is the Conventional Commits type in the PR title, so the next number can be read straight from the title.

**Example.** `dev` is at `0.20.1`, and three PRs are merged in this order:

1. `feat: dark mode` gives `0.21.0` (a feature: MINOR goes up and PATCH goes back to `0`).
2. `fix: dark mode contrast` gives `0.21.1`.
3. `docs: explain dark mode` gives `0.21.2`.

Releasing that state to `main` then gives `1.0.0`, and the next feature merged into `dev` gives `1.1.0`.

### Adding an entry

1. Each PR adds a new section at the top, right under the introduction, with the next version and the merge date: `## [0.21.0] - 2026-10-14`.
2. Under it go one or more of these headings, each with a short line that ends with the task and the PR number:
   - **Added:** something new.
   - **Changed:** something that already existed and now works differently.
   - **Fixed:** a bug.
   - **Security:** a new protection or a fixed risk.
3. Write each line for someone using the site or the panel, not for someone reading the code.
4. If another PR is merged first, the open PR is rebased and its version moves to the next free number.

When `dev` is released to `main`, the release gets a SemVer tag on `main` (`v1.0.0`), and its notes are the sections added since the previous release.
