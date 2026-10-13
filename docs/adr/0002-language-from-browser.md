# 0002 · Language from the browser, with country detection for later

Status: accepted · Date: 2026-10-11 · Decided by: Nicolas

## Context

The brief asks for the site in Spanish or in English depending on the visitor's location, with a manual switcher. Detecting the location requires a service or an IP (network address) database. For version 1, shipping on time matters more.

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. Country from Cloudflare (`CF-IPCountry` header, free plan) | ~1 h | DNS (domain name system) moves to Cloudflare; one more provider |
| B. Country by IP with MaxMind's GeoLite2 database | ~3 h plus monthly updates | More moving parts for the same result |
| C. Browser language (`Accept-Language`) | 0 h | It is the visitor's language, not their location |

## Decision

C in version 1 and A when the site grows. If the browser's first language is Spanish, the page is shown in Spanish; otherwise, in English. The switcher's choice is saved in `localStorage` and overrides everything else.

## Consequences

- There are no extra providers or additional work in version 1.
- A recruiter in Chile with the browser in English will see the page in English. That is acceptable, because it is the language they use.
- So that moving to A is a small change, the API decides the language in a single function, which receives the country (empty for now) and the `Accept-Language`. The visits table already has the `country` column.
