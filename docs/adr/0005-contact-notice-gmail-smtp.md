# 0005 · Contact notice via Gmail SMTP

Status: accepted · Date: 2026-10-11

## Context

Each contact message is saved in the database and also sent by email to the site owner, the only recipient.

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. Gmail SMTP with an app password | Free, ~30 min | Needs two-step verification; mail is sent from the owner's account |
| B. Resend (3,000 emails a month, 100 a day free) | Free, ~1 h | The domain must be verified with DNS records |

## Decision

A. Sending runs in a FastAPI background task, behind a single function in `app/services/mail.py`.

## Consequences

- A failed email doesn't lose the message: it is saved and shows in the panel with `emailed = false`.
- Sending to third parties later means switching to B inside that one function.
- The app password lives only in the server's `.env`.
