# 0009 · Efficient token use without losing quality

Status: accepted · Date: 2026-10-11 · Requested by: Nicolas

## Context

Development is done with Claude Code on a subscription with usage limits, and the automated AI review from ADR (architecture decision record) 0007 draws from the same subscription. The goal is to get the most out of every token. The condition is not to lose quality: tests, security and review are not cut to save tokens.

In practice, what costs the most isn't writing code: it's rereading context that isn't needed, long sessions that drag the whole history along, and redoing work when a task was poorly defined.

## Options considered

| Option | Savings | Cons |
|---|---|---|
| A. No rules: work however it goes | None | Long sessions, lots of repeated context, plan limits reached mid-week |
| B. Session, prompt and measurement rules (this ADR) | High in context and rework | Discipline: one task per session and filling in the log |
| C. Always use the cheapest model | High per token | More errors and rework on hard tasks, so the real savings are smaller |

## Decision

B, with these rules.

**Minimal context**

- CLAUDE.md has fewer than 200 lines and points to the documents in `docs/` instead of copying them. Each prompt says which document and which section to read.
- `node_modules/`, `dist/`, `.venv/`, the lockfiles and `/media` are blocked from reading in `.claude/settings.json`.
- Prompts name paths and functions; they don't paste content Claude can read on its own.
- Broad code searches are delegated to a subagent, which returns only the conclusion.

**Short sessions**

- One plan task per session. When it's done, `/clear` before the next one.
- If a session runs long, `/compact` with a note on what to keep.
- If a task isn't finished in two attempts, it is split into smaller tasks in the plan; it isn't retried with a longer prompt.

**Less rework**

- Tasks that touch several files start in plan mode: Claude proposes, Nicolas approves, and then the code is written.
- Each prompt comes from the `prompts/template.md` template, with the definition of done copied from the plan.
- The `pre-commit` hooks and the local tests run before the PR, so as not to spend an AI review or a CI (continuous integration) cycle on formatting errors.
- Test and lint output is requested in summary form (`pytest -q --maxfail=1`, only the lint errors).

**Model by task**

| Task type | Model |
|---|---|
| Routine: CRUD (create, read, update, delete), components, tests, configuration | Sonnet, mid-range |
| Design, hard bugs, security, or a task that failed once | Opus, the most capable |
| Automated PR (pull request) review | Sonnet, with the comment cap from ADR 0007 |

**Measurement**

- Each task records its tokens (`/cost`) in `prompts/log.md`.
- When each milestone closes, tokens and hours are compared with the plan, and what to adjust is noted in `docs/notes/`.
- If a milestone uses more than twice as much per task as the previous one, the prompts are reviewed before continuing.

**What is never cut**

Tests, minimum coverage, security checks, staging, human review, and the AI review of `feature/*` PRs.

## Consequences

- By the end of version 1 there will be real data on how much each type of task costs. With it, the template and the estimates for the next idea are adjusted.
- The session and model rules live in the product's CLAUDE.md, so Claude Code applies them without having to repeat them.
- Filling in the log takes ~2 minutes per task. Claude Code can do it at the end of the session if asked.
