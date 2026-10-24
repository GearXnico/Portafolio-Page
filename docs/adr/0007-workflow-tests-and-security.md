# 0007 · Workflow, testing and security

Status: accepted · Date: 2026-10-11 · Amended: 2026-10-18 (versioning)

## Context

The repository needs rules for branches, reviews, tests and security that CI enforces, with a readable linear history. It replaces the "`main` only" branching from [ADR 0006](0006-cicd-github-actions.md).

Most PRs are opened by a coding agent under the owner's GitHub account, and GitHub doesn't let a PR's author approve it, so a required approval needs a way through.

## Options considered

Branching:

| Option | Cost | Cons |
|---|---|---|
| A. `main` only, with short-lived branches | The lowest | Nowhere to integrate and test before publishing |
| B. `dev` for integration, `main` for releases, feature branches from `dev` | One extra PR per release | `dev` and `main` must be kept in sync |
| C. Full Git Flow with permanent `release/*` branches | Several PRs per release | Too much for a one-person project |

Required approval:

| Option | Cost | Cons |
|---|---|---|
| A. The merge is the approval: required PR and checks, no approvals | None | No approval is recorded |
| B. One required approval, with a bypass for the admin that GitHub records | One click per PR | The approval is the owner's explicit action |
| C. A second account that approves | ~1 h and another account | A formality |

## Decision

Branching B and approval B.

### Branches and history

| Branch | From | Into | Purpose |
|---|---|---|---|
| `main` | — | — | What is released |
| `dev` | `main` | `main` through a release PR | Integration; the default branch |
| `feature/<name>`, `fix/<name>`, `docs/<name>`, `chore/<name>` | `dev` | `dev` | Changes |
| `hotfix/<name>` | `main` | `main`, then `dev` | Urgent production fixes |

- Branch names are lowercase, hyphenated, in English, 2 to 4 words.
- Commits follow Conventional Commits (`feat`, `fix`, `test`, `docs`, `refactor`, `chore`). Each commit does one thing and keeps the tests green.
- PRs into `dev` are focused, ideally under 400 lines, use the template and merge with **rebase & merge**, so the history stays linear.
- Rebase & merge gives commits new SHAs on `main`. `sync-dev.yml` rebases `dev` onto `main` after every push to `main`, which drops the duplicates and brings hotfixes into `dev`; it is the only actor allowed to force-push `dev`.
- **Versions:** SemVer. PRs add entries under `## [Unreleased]` in `CHANGELOG.md`; the number is set when a release is cut (MINOR with a feature, PATCH otherwise; MAJOR stays 0 until 1.0.0). Before 2026-10-18 each PR set its own number.
- `main` and `dev` forbid deletion and force pushes (except `sync-dev.yml` on `dev`), require linear history, an up-to-date branch, green checks and one approval.
- `.env` files, keys and real data are never committed.

### Testing

| Level | Tool | Covers | Rule |
|---|---|---|---|
| API | pytest against real Postgres, `pytest-cov` | Endpoints, business rules, admin permissions | 80 % line coverage |
| Web | Vitest with Testing Library | Components with logic | 80 % line coverage |
| E2E | Playwright | Both languages, contact, admin login and editing | Every PR, against the compose stack |
| Static | `ruff`, `mypy`, `tsc --strict`, ESLint, Prettier | Format, common errors, types | No errors |

- Features come with tests; fixes start with a failing test.
- Tests are never skipped or disabled to get green; a flaky test is fixed in its own PR.
- API tests don't mock the database.
- `pre-commit` runs `ruff`, Prettier and private-key detection before each commit.

### Security

| Control | When | Fails on |
|---|---|---|
| Secret scanning with push protection | Every push | A secret in the push |
| CodeQL for Python, TypeScript and workflows | Every PR and weekly | A high or critical finding |
| `ruff` Bandit rules | Every PR | Any finding |
| `pip-audit` and `npm audit --audit-level=high` | Every PR and weekly | A high vulnerability |
| Trivy on the production images | Every PR | A high or critical vulnerability with a fix |
| Dependabot | Weekly | Doesn't block; its PRs pass the same checks |

Reviews also check that input is validated with Pydantic, that admin routes have a no-session test, and that logs hold no personal data.

### Automated review

`ai-review.yml` runs `anthropics/claude-code-action` when a PR to `dev` opens or is marked ready, and on an `@claude revisa` comment. It skips drafts, Dependabot and docs-only PRs. It reviews the diff against `docs/` and `AGENTS.md`, flags only real risks without proposing extra layers, leaves at most about 10 comments by severity, never approves and never blocks the merge.

### Deployment check

Every PR runs `deploy-check`: the production stack on the CI runner with the PR's images, the E2E suite and the health checks. Release PRs to `main` also require staging green on the same SHA ([ADR 0008](0008-staging-environments.md)).

### Definition of done

- [ ] New or updated tests, with coverage above the minimum
- [ ] CI, security and E2E green
- [ ] No secrets or personal data
- [ ] Docs updated when something visible changes, and an entry under `[Unreleased]`
- [ ] Branch up to date with its base
- [ ] Automated review comments addressed or answered
- [ ] Approved, or merged with a recorded bypass

## Consequences

- Nothing reaches `dev` without tests and security checks.
- The history of `dev` and `main` is linear, at the cost of tidy commits before each PR and a `dev` resync after each release.
- CI takes about 8 to 10 minutes with E2E and scans, and stays free on a public repository.
