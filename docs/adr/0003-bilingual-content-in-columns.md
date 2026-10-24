# 0003 · Bilingual content in `_es` and `_en` columns

Status: accepted · Date: 2026-10-11

## Context

All editable content (profile, experience, projects and image alt text) exists in Spanish and English. The two languages are fixed.

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. A column per language (`title_es`, `title_en`) | The lowest | A third language needs a migration per table |
| B. A translations table (entity, field, language, text) | ~4 h more across the API and the panel | More complex queries and forms |
| C. Translation files in the frontend | Low for fixed text | Content can't be edited from the panel |

## Decision

A for database content. Fixed UI text lives in `web/src/i18n/{es,en}.json`, which the panel doesn't edit.

## Consequences

- The panel shows both languages side by side, which makes a missing translation obvious.
- The API returns both languages and the frontend picks one, so switching language needs no new request.
- A third language would cost a migration per table, which is accepted because none is planned.
