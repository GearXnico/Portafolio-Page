# Development rules

How this repository is built. This is the short version: the reasoning behind each rule is in ADR (architecture decision record) 0007, and the commands are in the README.

## Principle

**No overengineer. Keep it simple and secure.** Between two secure solutions, pick the simpler one. Security is not cut back: it is solved with the most direct thing that works.

The underlying idea is that the project owner can read any part of the code and understand what it does and why. Code nobody understands cannot be maintained or defended in an interview.

## What gets built now

- Only what the task at hand needs.
- If it needs something new (a table, a service, a dependency), agree on it first and record the decision in an ADR when it has lasting impact.

## When not to create a layer

Before adding an abstraction, a configuration variable or a new file, go through this list. If the answer is "no", it is not added.

| Before... | Ask yourself | Example of "no" |
|---|---|---|
| Extracting a shared function or class | Are there already three places that use it the same way? | Two routes with a similar `if`: leave it repeated |
| Adding an environment variable | Does it change between local, staging and production, or is it a secret? | The maximum length of a message goes in the code |
| Creating a table or column | Does the plan or the data model in `docs/architecture.md` ask for it? | A users table when there is a single administrator (ADR 0004) |
| Adding a dependency | Is what is already installed not enough, and does it pass `pip-audit` or `npm audit`? | A date library to format month and year |
| Making something configurable | Are there two real cases today? | Supporting a third language "just in case" when the brief asks for Spanish and English |

There are two exceptions, decided on purpose: the language is decided only in `api/app/services/locale.py` (ADR 0002) and email is sent only from `api/app/services/mail.py` (ADR 0005). They are a single point because they are known to change.

## Where each thing goes

The full map is in the README. When writing code:

- **API (application programming interface):** the route in `app/routers/` only receives, calls and responds. The logic goes in `app/services/`, validation of what comes in and goes out in `app/schemas/` (Pydantic) and the tables in `app/models/`.
- **Web:** one page per file in `src/pages/`, one component per file in `src/components/`, API calls in `src/api/` and texts in `src/i18n/es.json` and `en.json`, never written inside a component.
- **Names and language:** code, tests, code comments and documentation in English; user-facing texts in both languages, from `src/i18n/`.
- **Comments:** they explain the why, not the what. Each file in `services/` opens with a paragraph that says what it is responsible for.

## Branches, commits and PRs (pull requests)

Summary of ADR 0007:

1. Start from `dev` on a `feature/`, `fix/`, `docs/` or `chore/` branch with 2 to 4 English words, lowercase and hyphenated, for example `feature/contact-form`. `hotfix/` branches off `main`.
2. Commits in English with Conventional Commits (a standard message format): `feat: add contact form`. Each commit does one thing and leaves the tests green, because it reaches `dev` as is.
3. One PR per plan task, into `dev`, ideally under ~400 lines, in English and with the template: Before, After, How to test and the checklist.
4. Merge only with rebase & merge, and delete the branch afterwards.
5. Never push secrets, `.env` or personal data: the repository is public.

## How a PR is reviewed

1. **CI (continuous integration):** tests, lint, types, security and E2E (end-to-end tests) must be green. Without that, it cannot be merged.
2. **AI (artificial intelligence) review:** `ai-review.yml` leaves comments on code PRs, never approves and does not block. Each comment is fixed or answered in its thread.
3. **Owner review:** reads the PR in this order and approves it (or merges with a recorded bypass) only if the answer to everything is yes:
   - Does it do what the task asks, and nothing more?
   - Do I understand every file that changed? If not, ask for an explanation in the PR before going on.
   - Is it the simplest thing that works? (table above)
   - Are inputs validated, do `/api/admin/*` routes require a session, and do the logs keep personal data out?
   - Do the tests test what matters? (`docs/testing.md`)
   - Are the README or `docs/` up to date if something visible changed?

To understand a large PR, it helps to read it commit by commit: each one does one thing and its message says which.
