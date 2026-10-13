# 0003 · Bilingual content in `_es` and `_en` columns

Status: accepted · Date: 2026-10-11 · Proposed by: Claude, approved with the architecture

## Context

All editable content (profile, experience, projects and the images' alt text) exists in Spanish and in English. These are two fixed languages, and there are no plans to add more.

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. Columns per language (`title_es`, `title_en`) | The lowest | Adding a third language requires a migration per table |
| B. Translations table (entity, field, language, text) | ~4 h extra across the API and the panel | More complex queries and forms |
| C. Translation JSON files in the frontend | Low for fixed text | The content couldn't be edited from the panel |

## Decision

A for the database content. The UI's fixed text (buttons and headings) goes in JSON files in the frontend, which aren't edited from the panel.

## Consequences

- The panel form shows both languages side by side, which helps not to forget a translation.
- The API (application programming interface) returns both languages and the frontend chooses which one to show, so switching languages doesn't require another call.
- A third language would cost a migration per table. This is accepted because it isn't planned.
