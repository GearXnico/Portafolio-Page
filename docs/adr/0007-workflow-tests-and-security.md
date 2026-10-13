# 0007 · Workflow, testing and security

Status: accepted · Date: 2026-10-11 · Requested by: Nicolas

## Context

Nicolas asked for these rules for the site's repo, which the template later inherits:

- Mandatory testing to approve into `dev`, automated with CI/CD (continuous integration and continuous deployment).
- Security validation.
- `feature/descriptive-name` branches.
- PRs (pull requests) with approval, and later a deployment check.
- Good development and version control practices.
- During the review he added two requests: a staging environment, which ADR 0008 addresses, and that every merge to `dev` or `main` be done with rebase & merge, for a clearer commit history.

This ADR (architecture decision record) replaces the "`main` only" rule from 0006.

There is a GitHub limitation: a PR's author can't approve it. The PRs Claude opens are under Nicolas's name, so a mandatory approval would block them. Nicolas chose how to solve it on 2026-10-11.

## Options considered

On the branching model:

| Option | Cost | Cons |
|---|---|---|
| A. `main` only, with short-lived branches (what 0006 proposed) | The lowest | No branch to integrate and test in before publishing |
| B. `dev` for integration and `main` for production, with `feature/*` branches from `dev` | One extra PR per published release | `dev` and `main` have to be kept in sync |
| C. Full Git Flow (permanent `release/*` and `hotfix/*` branches) | Several PRs per release | Overkill for one person |

On mandatory approval:

| Option | Cost | Cons |
|---|---|---|
| A. Your merge is the approval: mandatory PR and checks, no approvals | None | No formal approval is recorded in GitHub |
| B. 1 mandatory approval with a bypass only for you: you merge by ticking "bypass" and GitHub records it | One extra click per PR | The approval is your explicit action, not someone else's |
| C. A second account (bot or collaborator) that approves | ~1 h and one more account | Approving with another account of yours is just a formality |

## Decision

- **Branching model: B**, because it is what Nicolas asked for.
- **Approval: B, 1 approval with a recorded bypass** (Nicolas, 2026-10-11). `main` and `dev` require 1 approval, and only Nicolas can skip it, by ticking the bypass when merging; GitHub records every bypass. When the factory's agents open PRs with their own account, Nicolas will approve them normally.

### Branches and version control

| Branch | Branches off | Merges into | Purpose |
|---|---|---|---|
| `main` | — | — | What is published. Every merge deploys to production. |
| `dev` | `main` | `main` through a release PR | Integration. It is the repo's default branch, and every merge deploys to staging (ADR 0008). |
| `feature/<descriptive-name>` | `dev` | `dev` | New functionality, for example `feature/contact-form` |
| `fix/<name>` | `dev` | `dev` | Fix |
| `docs/<name>`, `chore/<name>` | `dev` | `dev` | Documentation, configuration and dependencies |
| `hotfix/<name>` | `main` | `main` and then `dev` | Urgent fix in production |

Names are lowercase, hyphenated, in English and 2 to 4 words long. Documentation, commit messages and PR text are also in English (Nicolas, 2026-10-13: documentation, commits, branches and PRs in English).

1. **Commits:** Conventional Commits (a standard message format) is used, for example `feat: add contact form` or `fix: correct default language`. The types are `feat`, `fix`, `test`, `docs`, `refactor` and `chore`.
2. **PRs to `dev`:**
   - One per feature, ideally with fewer than ~400 changed lines.
   - Uses the repo's template: Before, After, How to test and the definition-of-done checklist.
   - Merged with **rebase & merge**: the branch's commits are copied one by one onto `dev`, without merge commits, and the history stays linear.
   - Since each commit lands as is, before opening the PR they are tidied up with `git rebase -i`: each commit does a single thing, follows Conventional Commits and leaves the tests green.
   - The branch is deleted after the merge.
3. **Release PR `dev` → `main`:** also with **rebase & merge**. It requires staging to be healthy with the same SHA (ADR 0008). After the deployment, a SemVer (semantic versioning) tag (`v1.2.0`) is created, with the release notes in `CHANGELOG.md`.
   - **Watch out:** GitHub rewrites every commit on rebase & merge, so in `main` they end up with a different SHA (identifier) than in `dev`. If this isn't corrected, the next release PR shows repeated commits or conflicts.
   - To avoid it, the `sync-dev.yml` workflow runs after every push to `main` and runs `git rebase main` on `dev`. Git drops only the commits that are already in `main` and keeps the new ones. Then it runs `git push --force-with-lease` to `dev`. It is the only actor with a bypass of the "no force push" rule on `dev`.
   - A `hotfix/*` goes into `main` and reaches `dev` through that same workflow.
4. **Versions** (Nicolas, 2026-10-13): every PR merged into `dev` has a version in SemVer format (`MAJOR.MINOR.PATCH`) and records it in `CHANGELOG.md`. A `feat` PR bumps MINOR and a PR of any other type bumps PATCH. MAJOR counts the releases to `main` and stays at `0` until the first one, `1.0.0`. The guide, with an example, is at the end of `CHANGELOG.md`.
4. **Protection of `main` and `dev`:**
   - No force push or deletion (except `sync-dev.yml` on `dev`).
   - Linear history required, and rebase & merge as the only enabled merge method.
   - Mandatory PR with 1 approval; the bypass is allowed only for Nicolas.
   - The checks below have to be green.
   - The branch has to be up to date with its base before merging.
   - On your own `feature/*` branch, `git push --force-with-lease` is allowed.
5. **Never in the repo:** `.env`, keys or real data. Only `.env.example` is versioned.

### Testing (requirement to merge into `dev`)

| Level | Tool | What it covers | Rule |
|---|---|---|---|
| API (application programming interface) | pytest 9 with real Postgres in CI and `pytest-cov` | Endpoints, business rules, `/api/admin/*` permissions | Minimum coverage of 80 % of lines; if it drops, the check fails |
| Frontend | Vitest 5 with Testing Library | Components with logic: language switcher, forms, panel | Minimum coverage of 80 % (it was 60 %; Nicolas raised it on 2026-10-12) |
| E2E (end-to-end) | Playwright 1.64 | The page loads in both languages, the contact form, and logging in plus creating a project in the panel | Runs on every PR, against the `compose` stack started on the runner |
| Types and style | `ruff`, `mypy`, `tsc --strict`, ESLint and Prettier | Formatting, common errors and types | No errors |

The testing rules are:

- Each `feature/*` comes with its tests.
- Each `fix/*` comes with a test that reproduces the bug before fixing it.
- A test is never skipped or disabled to get CI green. A flaky test is fixed in its own PR.
- The database is not replaced by mocks in the API tests: they run against real Postgres.
- `pre-commit` 4.6 runs `ruff`, Prettier and private key detection before each commit, to catch errors before CI.

### Security validation

| Control | When | The check fails if |
|---|---|---|
| GitHub secret scanning with push protection (free on public repos) | On every push | Someone tries to push a secret (it blocks the push) |
| CodeQL (GitHub's static analysis) for Python and TypeScript | On every PR and every week | There is a high or critical severity finding |
| `ruff` security rules (Bandit's) | On every PR | There is any finding |
| `pip-audit` 2.10 and `npm audit --audit-level=high` | On every PR and every week | There is a dependency with a high vulnerability |
| Trivy (Docker image scanner) | On every PR, on the built images | There is a high or critical vulnerability with a fix available |
| Dependabot (alerts and update PRs) | Every week | It doesn't block; its PRs go through the same checks |

On every PR, these checklist items are also reviewed by hand:

- Inputs are validated with Pydantic.
- Admin routes have a test that checks access without a session.
- No personal data is written to the logs.

### Automated AI review

On 2026-10-11, Nicolas asked for an agent to review PRs so that nothing important slips past his own review.

- **Tool:** `anthropics/claude-code-action@v1` in the `ai-review.yml` workflow.
- **Authentication:** `CLAUDE_CODE_OAUTH_TOKEN`, generated with `claude setup-token`. With it, usage is deducted from the Claude subscription instead of being charged per token. If an API key is used later, it is billed separately.
- **When it runs:** when a PR to `dev` is opened and when it is marked ready for review, not on every push. It can also be requested again by commenting `@claude revisa`.
- **When it doesn't run:** on PRs that only change documentation (`docs/**`, `*.md`), on Dependabot's, and on drafts.
- **What it reviews:** the diff, against the rules in `docs/` (ADRs, architecture) and in `CLAUDE.md`: bugs, security, missing tests and rules not followed.
- **Criteria (Nicolas, 2026-10-12):** "no overengineer" and "keep it simple and secure". It flags as important only what is a real risk, and it doesn't propose extra layers or abstractions if the simple option is already secure.
- **How it responds:** only with comments, at most about 10, ordered by severity. **It never approves**, so that the approval from ADR 0007 (your recorded bypass) stays your decision and isn't triggered by a bot.
- **It doesn't block the merge:** it is an aid for your review, not a required check.

Estimated cost, not measured: per PR of 300 to 800 lines, between 40,000 and 120,000 input tokens and between 3,000 and 8,000 output tokens. With caching and a mid-range model, about a third less. With about 25 PRs in version 1, that would be on the order of 1 to 3 million input tokens in total. It is measured on the first 5 PRs and, if it uses too much of your plan, the comment cap is lowered or it is limited to `feature/*` PRs.

### Deployment check

There are two levels, and the details are in ADR 0008:

1. **On every PR to `dev`:** the `deploy-check` job starts `compose.prod.yml` on the CI runner, with the PR's images, and runs the E2E tests and `GET /api/health`.
2. **On the release PR to `main`:** staging is required to be deployed with the same SHA and its E2E tests must be green.

### Definition of done for a PR

- [ ] New or updated tests, with coverage above the minimum
- [ ] CI, security and E2E green
- [ ] No secrets or personal data
- [ ] Documentation updated if something visible changes (README or docs/)
- [ ] Branch up to date with its base
- [ ] Automated review comments addressed or answered
- [ ] Approved, or merged by Nicolas with a recorded bypass

## Consequences

- Nothing reaches `dev` without tests and security checks, and nothing reaches `main` without going through staging.
- The history of `dev` and `main` is linear. In exchange, each commit has to be clean before the PR, and `dev` resyncs itself after every release.
- CI goes from ~5 to about ~8-10 minutes because of the E2E tests and the scans. It stays free on a public repo.
- Setting all this up adds about 6 h to milestone 1 of the plan, and `sync-dev.yml` adds ~1 h. With staging (ADR 0008), the estimate goes up from 80 to ~92 h.
- The rules live in the template and in CLAUDE.md, so Claude Code follows them in every new product.
