# Development

How the code is organized, how changes reach `dev` and `main`, and what CI enforces. The reasoning behind these rules is in [ADR 0007](adr/0007-workflow-tests-and-security.md).

## Principle

Keep it simple and secure. Between two secure solutions, pick the simpler one; security is never traded away, it is solved with the most direct thing that works. Every part of the code should be readable and explainable by whoever maintains it.

## When not to add a layer

Before adding an abstraction, a setting or a new file, check it against this table. If the answer is no, it is not added.

| Before... | Ask | Example of "no" |
|---|---|---|
| Extracting a shared function or class | Do three places already use it the same way? | Two routes with a similar `if` stay repeated |
| Adding an environment variable | Does it differ between environments, or is it a secret? | The maximum message length lives in the code |
| Creating a table or column | Does the data model need it? | A users table for a single administrator ([ADR 0004](adr/0004-single-admin.md)) |
| Adding a dependency | Is what is installed not enough, and does it pass `pip-audit` or `npm audit`? | A date library to format month and year |
| Making something configurable | Are there two real cases today? | A third language "just in case" |

Two places are single points on purpose, because they are expected to change: the language is decided only in `api/app/services/locale.py` ([ADR 0002](adr/0002-language-from-browser.md)) and email is sent only from `api/app/services/mail.py` ([ADR 0005](adr/0005-contact-notice-gmail-smtp.md)).

## Where code goes

- **API:** routes in `app/routers/` only receive, call a service and respond. Logic lives in `app/services/`, input and output validation in `app/schemas/`, tables in `app/models/`.
- **Web:** pages in `src/pages/`, one component per file in `src/components/`, API calls in `src/api/`, UI text in `src/i18n/{es,en}.json`.
- **Language:** code, names, comments and docs in English; user-facing text in both languages.
- **Comments:** only for a non-obvious why. Clear names come first.

## Branches, commits and PRs

1. Branch from `dev`: `feature/`, `fix/`, `docs/` or `chore/` plus 2 to 4 lowercase words, for example `feature/contact-form`. `hotfix/` branches from `main`.
2. Conventional Commits: `feat: add contact form`. Each commit does one thing and keeps the tests green, because it reaches `dev` as is.
3. One focused PR into `dev`, ideally under 400 lines, using the template: Before, After, How to test and the checklist.
4. Each PR adds its entry under `## [Unreleased]` in `CHANGELOG.md`; the version is set when a release is cut.
5. Merges use rebase & merge only.
6. No secrets, `.env` files or personal data: the repository is public.

## Review

1. **CI** must be green: tests, lint, types, security and E2E.
2. **Automated review:** `ai-review.yml` comments on code PRs with Claude. It never approves and doesn't block. It skips drafts, Dependabot and docs-only PRs; commenting `@claude revisa` asks for another pass. It needs the `CLAUDE_CODE_OAUTH_TOKEN` secret and the Claude GitHub app.
3. **Owner review** checks that the PR:
   - does what it says and nothing more;
   - is the simplest thing that works;
   - validates input, requires a session on `/api/admin/*` and keeps personal data out of logs;
   - tests what matters ([testing.md](testing.md));
   - updates the docs when something visible changes.

## CI

`ci.yml` runs on every PR and every push to `dev` and `main`. A new push to the same PR cancels the previous run. It uses no secrets and a read-only token, actions are pinned by SHA, and pip, npm and pre-commit are cached.

| Job | What it checks |
|---|---|
| pre-commit | `ruff` (lint, format and the Bandit `S` rules), Prettier and committed private keys |
| API | `mypy` and `pytest` against Postgres, with 80 % coverage |
| Web | ESLint, `tsc`, Vitest with 80 % coverage and `vite build` |
| E2E | Playwright against the dev server, with the database, migrations and API from the compose stack |
| Deployment (`deploy-check`) | Builds the production images, deploys them with `deploy/deploy.sh`, forces a failed deploy and checks the rollback, checks that no container runs as root, restores an encrypted backup and runs the E2E suite against Caddy |

The same pre-commit hooks run locally:

```bash
pip install "pre-commit==4.6.*"
pre-commit install
pre-commit run --all-files
```

## Security checks

`security.yml` runs on every PR, every push to `dev` and `main`, and every Monday at 09:00 UTC.

| Job | Scope | Fails on |
|---|---|---|
| CodeQL | Python, TypeScript and the workflows | A high or critical finding |
| pip-audit | API dependencies, including dev ones | Any known vulnerability |
| npm audit | Web dependencies from `package-lock.json` | A high or critical vulnerability |
| Trivy | The production images | A high or critical vulnerability with a fix that `.trivyignore` doesn't accept |

Each entry in `.trivyignore` has an expiry date (`exp:`), after which the job fails again and the finding is reviewed. `pip-audit` and `npm audit` don't read that file, so our own dependencies are still checked.

`dependabot.yml` checks pip, npm, the base images and the actions weekly. Minor and patch updates come as one PR per ecosystem, majors one by one, and new versions wait 7 days before being proposed; security alerts don't wait.

Secret scanning and push protection are enabled in the repository settings. CodeQL's default setup stays off, because `security.yml` is the advanced setup and GitHub doesn't allow both.

Locally:

```bash
cd api && pip install "pip-audit==2.10.*" && pip-audit --skip-editable
cd web && npm audit --audit-level=high
```

## Branch protection

`dev` and `main` are protected by three rulesets, versioned in `.github/rulesets/` so they can be re-imported from Settings > Rules > Rulesets.

| Ruleset | Branch | Rules | Bypass |
|---|---|---|---|
| `main` | `main` | No deletion or force push, linear history, PR required, rebase & merge only, the `ci.yml` and `security.yml` checks green on an up-to-date branch | None |
| `dev` | `dev` | Same as `main` | The `sync-dev.yml` deploy key |
| `aprobacion` | `dev` and `main` | One approval, dismissed by a new push | Repository admin, with a recorded bypass, and the deploy key |

Approval lives in its own ruleset so a bypass skips only the approval, never the checks. When a job is renamed or added, its ruleset JSON and the ruleset in GitHub change in the same PR; otherwise the required check stays pending.

### `sync-dev.yml`

After each push to `main` (a release or a hotfix), it rebases `dev` onto `main` and force-pushes it. That drops the copies that rebase & merge leaves on `main` with new SHAs and brings hotfixes into `dev`. On a conflict it fails without pushing, and the conflict is resolved by hand.

It uses a deploy key with write access, stored as the `SYNC_DEV_SSH_KEY` secret:

```bash
ssh-keygen -t ed25519 -N "" -C sync-dev -f sync-dev
```

Add `sync-dev.pub` under Settings > Deploy keys with write access, save the private key as the secret, and delete both files.
