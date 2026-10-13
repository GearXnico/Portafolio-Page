# Testing rules

What is tested, what is not, and why each type of test exists. The commands are in the README and the mandatory rules in ADR (architecture decision record) 0007.

## What tests are for here

A test is worth it if it fails when something that matters breaks. In this project two things matter:

1. **What the visitor and the administrator see:** that the page loads with its content, in their language, and that the panel lets them edit it.
2. **Rules that can break silently:** the ones that, if they fail, nobody notices by looking at the page, but that open a security or data problem. For example, a panel route that responds without a session.

Every new test must protect one of those two things. Otherwise, it is not written.

## The types of test and why each one exists

| Type | Tool | Where | Why it exists |
|---|---|---|---|
| E2E (end-to-end test) | Playwright | `web/e2e/` | It is the only one that tests the whole system the way a person uses it: browser, Caddy, API and database. If something between the pieces gets disconnected, only this one sees it. |
| API (application programming interface) | pytest against real Postgres | `api/tests/` | Tests the business and security rules of each route, quickly and without a browser. It runs against real Postgres because several rules live in the database (constraints, API user permissions) and a mock (simulated object) would hide them. |
| Web components | Vitest and Testing Library | `web/tests/` | Tests the page logic that does not need the API: what is shown for each response, the language, the links. Runs in seconds. |
| Static | ruff, mypy, `tsc`, ESLint and Prettier | CI (continuous integration) and pre-commit | Catch type errors, style errors and insecure patterns without running anything. |
| Production on the runner | `deploy-check` job | `.github/workflows/ci.yml` | Brings up `deploy/compose.prod.yml` and runs the E2E tests against it, to know that what gets deployed starts. |

Rule of thumb for choosing the level: **a case is tested once, at the lowest level that can see it**. A validation of a field goes in pytest; the full form reaching the database goes in an E2E test. The same case is not repeated at all three levels.

## What is always tested

| Rule | Why | Where it is tested today |
|---|---|---|
| Every `/api/admin/*` route responds 401 without a session | A new route outside the protected router would leave the panel open | `test_admin_login.py` (walks every route). `test_admin_content.py` repeats it for the content routes with an empty body, to also check that the 401 comes before the 422; PR (pull request) #24 proposes merging them |
| Login: correct password, wrong password, lockout after 5 attempts, invalid or expired session | It is the panel's only door | `test_admin_login.py` |
| On the web, `/admin` without a session leads to the login, and login and logout show what matches each API response | If it fails, the panel looks empty or broken instead of asking for the password (the API still responds 401) | `web/e2e/admin.spec.ts` (redirect, and logging in and out with the real password) and `web/tests/admin.test.tsx` (messages and logout) |
| Screenshot validation: real file type, 5 MB, pixels, metadata | An uploaded file is the most dangerous input | `test_admin_content.py` |
| Submission limits: 5 messages per hour per IP, honeypot (trap field), body size | Without them the form fills up with spam | `test_contact.py` and `test_rate_limit.py` |
| The real IP behind Caddy, and that `X-Forwarded-For` is not trusted without a trusted proxy | If it fails, an attacker bypasses the limits by changing a header | `test_contact.py` (contact) and `test_admin_login.py` (login): they are two cases, one per route, because each one can be misconfigured separately |
| Every invalid input responds 422 | Pydantic validates, but the test confirms the schema is the right one | One test per resource |
| What must not leak does not leak: profile email, visitor IP, internal ids | A personal data leak is not visible on the page | `test_bootstrap.py` and `test_admin_content.py` |
| The API user cannot change tables | Limits the damage of a SQL injection | `test_db_permissions.py` |
| Migrations apply, roll back and match the models | A broken migration takes down the deployment | `test_migrations.py` |
| A message sent from the contact form reaches the API and is saved | It is the only way to make contact; if the form and the API stop matching, nobody is warned | `web/e2e/contact.spec.ts` (the 201 arrives only after saving, as `test_contact.py` proves) |
| A visit with UTM (Urchin Tracking Module) parameters is recorded with its source: the page reads the UTM parameters from the URL and passes them to `bootstrap` and to the contact form | Without the source there is no way to know which job application link worked | `web/e2e/utm.spec.ts` (they reach the API through the proxy), `web/tests/utm.test.ts` (cleanup and length) and `test_bootstrap.py` and `test_contact.py` (they are saved) |
| The page loads, switches language, has no console errors and is not missing security headers | It is what any visitor sees | `web/e2e/` |
| Title, `meta description` and `<html lang>` follow the page language | It is what search engines and screen readers read | `web/tests/HomePage.test.tsx`, `web/tests/admin.test.tsx` and `web/e2e/lang.spec.ts` |
| A project created in the panel shows up on the public page, and the form sends both languages and only the fields the API accepts | It is the panel's main task; if the form and the API stop matching, the project is not saved | `web/e2e/projects.spec.ts` (the full path) and `web/tests/adminProjects.test.tsx` (what is sent and the error messages) |
| A profile change made in the panel shows up on the page; the profile, skills and experience forms send both languages and only the fields the API accepts, and warn if it responds 422 | It is what the administrator does to keep the page up to date; if the form and the API stop matching, the change does not arrive and nobody notices | `web/e2e/profile.spec.ts` (profile end to end) and `web/tests/adminProfile.test.tsx` (forms) |
| Messages and visits in the panel: message list, mark as read (422 if the body is not a strict boolean, 404 if it does not exist) and counts by `utm_source` and `utm_campaign` | It is how the administrator knows which link brought visits and contacts; a badly grouped count is not noticeable at a glance | `test_admin_activity.py` (grouping and reading against the database), `web/tests/activity.test.tsx` (what each screen shows) and `web/e2e/activity.spec.ts` (a visit with UTM and a test message show up in the panel) |
| A screenshot uploaded from the project form shows up on the public page; uploading or deleting it does not discard what is not yet saved in the form | It is the criterion of task 4.3, and a form that rebuilds itself in the middle of an edit loses changes without warning | `web/e2e/images.spec.ts` (the full path; against Caddy it also checks that the file is served as WebP) and `web/tests/projectImages.test.tsx` (what is sent, the delete confirmation and the 413, 415 and 422 errors) |

Each `fix/*` starts with a test that reproduces the bug and fails before the fix.

## What is not tested

- **What the libraries already test:** that FastAPI returns JSON or that React renders. What is tested is that *our* schema rejects what it should.
- **Styles and exact texts:** colors, margins or the wording of a title. What is tested is that the text comes from the right language, not what it says.
- **Code without logic:** a model that only declares columns, a component that only draws what it receives.
- **The same case at several levels:** see the rule of thumb above.
- **Internal details:** what is tested is what goes in and what comes out (the response, the row in the database), not how the function does it inside. That way a refactor does not break tests.

## Coverage

**Tests must cover at least 80% of the lines of code**, in the API and in the web (ADR 0007). If a PR drops below that minimum, CI fails and it cannot be merged.

The minimum is mandatory, but it is not the goal: it ensures no code is left untested, not that what matters has been tested. That is what the tables above are for. If coverage is missing, add tests for what matters in the new code, not empty tests that only raise the number.

## How to write a test

- **An English name that states the behavior:** `test_blocks_after_5_failed_attempts`, not `test_login_3`. Reading the list of names tells you what the system does.
- **One behavior per test**, in three parts: arrange, act and assert.
- **Fake, clear data:** documentation IPs (`203.0.113.7`), `@example.com` emails. Never real data.
- **Never** skip, disable or delete a test to make CI green. A flaky test is fixed in its own PR.
- If a test becomes redundant, propose deleting it in the PR and the project owner confirms.
