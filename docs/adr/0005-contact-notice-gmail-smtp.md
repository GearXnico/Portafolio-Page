# 0005 · Contact notice via Gmail SMTP

Status: accepted · Date: 2026-10-11 · Decided by: Nicolas

## Context

Each message from the contact form is saved in the database and also has to reach Nicolas by email. He is the only recipient.

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. Gmail SMTP (Simple Mail Transfer Protocol) with an app password | Free, ~30 min | Requires two-step verification; the email is sent from his own account |
| B. Resend (3,000 emails a month and 100 a day for free) | Free, ~1 h | The domain has to be verified with DNS (domain name system) records |

## Decision

A. Sending runs in a FastAPI background task and sits behind a single function.

## Consequences

- If the email fails, the message is still saved and shows up in the panel (`emailed` column).
- If sending email to third parties is needed later, it switches to B by touching only that function.
- The app password lives only in the server's `.env`.
