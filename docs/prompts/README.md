# Development prompts · Portfolio website

Every prompt used with Claude Code for a plan task is kept here: what was asked, how much it cost and what was learned. It serves three purposes:

- Reuse the prompts that worked in the next idea.
- Measure token usage per task (ADR (architecture decision record) 0009).
- See the development progress prompt by prompt.

## How to use it

1. Before starting a plan task, copy `template.md` to `NNNN-<task>.md`, for example `0001-monorepo-structure.md`, and fill it in. The number is sequential.
2. Paste the "Prompt" block into a new Claude Code session.
3. When done, fill in the "Result" section of the file and add a row to `log.md`.
4. If the prompt had to be corrected, keep the version that worked and note under "Lessons" what changed.

Claude Code can fill in the log at the end of each session if asked: "add this task's row to `prompts/log.md` with the usage from `/cost`". That instruction lives in the product's CLAUDE.md.
