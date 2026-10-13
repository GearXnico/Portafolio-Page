# NNNN · <plan task>

Plan task: <number, for example 1.2> · Date: YYYY-MM-DD · Model: <Sonnet / Opus> · Branch: `feature/<name>`

## Prompt

```
Task <number> of the plan (docs/plan.md): <task title>.

Context: read only docs/plan.md (task <number>) and <applicable ADR or architecture section>. Don't read other documents unless you need them.

What to do:
- <concrete step 1>
- <concrete step 2>

Done when: <definition of done copied from the plan>.

Constraints:
- Follow CLAUDE.md (branches, commits, tests, security).
- Run the tests and the lint before finishing and show me only the summary.
- If something in the plan doesn't match the code, ask me before changing the design.

When done: open the PR to dev and give me the link.
```

## Result

- PR (pull request): <link>
- Tokens (from `/cost`): <input> / <output> · Duration: <min>
- Finished in one session?: yes / no (why)
- Attempts: <1, 2…>

## Lessons

- <What worked, what had to be clarified and what to change in the prompt next time.>
