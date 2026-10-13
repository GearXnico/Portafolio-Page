# 0004 · Single admin with credentials in environment variables

Status: accepted · Date: 2026-10-11 · Proposed by: Claude, approved with the architecture

## Context

The admin panel has a single user, Nicolas. Multiple admins or roles were left out of the MVP (minimum viable product).

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. Email and Argon2 password hash in environment variables; session with a JWT (JSON Web Token, a signed token) in an `httpOnly` cookie | ~3 h | Changing the password requires editing the server's `.env` and restarting |
| B. Users table with sign-up and password recovery | ~8 h | Code and risks that aren't needed |
| C. Login with GitHub (OAuth, delegated authorization) | ~5 h | Depends on GitHub and adds configuration |

## Decision

A. The cookie is `httpOnly`, `Secure` and `SameSite=Strict`, and lasts 7 days. Login allows at most 5 failed attempts every 15 minutes per IP (network address). The visitor's real IP is taken from `X-Forwarded-For` only when the connection comes from Caddy: `TRUSTED_PROXIES` in the production `.env`, set to the internal Docker network (Nicolas's decision, 2026-10-12, because it is the simplest and most secure option). The same applies to the contact form's rate limit.

## Consequences

- There is no users table and no password recovery flow. If the password is forgotten, a new hash is generated with a command and the `.env` is updated.
- The `SameSite=Strict` cookie, together with the frontend and the API (application programming interface) sharing a domain, avoids having to set up CORS (cross-origin resource sharing, the browser's cross-domain restriction) and CSRF (cross-site request forgery) protection separately.
- If more admins are needed later, it migrates to B without changing the rest of the API.
