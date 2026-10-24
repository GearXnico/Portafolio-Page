# 0004 · Single admin with credentials in environment variables

Status: accepted · Date: 2026-10-11

## Context

The admin panel has one user. Multiple admins and roles are out of scope.

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. Email and Argon2 hash in environment variables; JWT session in an `httpOnly` cookie | ~3 h | Changing the password means editing the server's `.env` and restarting |
| B. Users table with sign-up and password recovery | ~8 h | Code and risk that aren't needed |
| C. Login with GitHub OAuth | ~5 h | Depends on GitHub and adds configuration |

## Decision

A. The cookie is `httpOnly`, `Secure` and `SameSite=Strict` and lasts 7 days. Login allows at most 5 failed attempts per IP every 15 minutes. The client IP comes from `X-Forwarded-For` only when the connection comes from Caddy's internal network (`TRUSTED_PROXIES`); the contact form's rate limit uses the same IP.

## Consequences

- No users table and no recovery flow: a forgotten password is replaced by generating a new hash with `python -m app.hash_password` and updating `.env`.
- The `SameSite=Strict` cookie, with the page and the API on the same origin, removes the need for CORS and separate CSRF protection.
- More admins would move to B without changing the rest of the API.
