# 0002 · Language from the browser, with country detection for later

Status: accepted · Date: 2026-10-11

## Context

The site is shown in Spanish or English, with a manual switch. Choosing by the visitor's location needs a geolocation service or an IP database; the browser's language is available for free in every request.

## Options considered

| Option | Cost | Cons |
|---|---|---|
| A. Country from Cloudflare (`CF-IPCountry` header, free plan) | ~1 h | DNS moves to Cloudflare; one more provider |
| B. Country by IP with MaxMind GeoLite2 | ~3 h plus monthly updates | More moving parts for the same result |
| C. Browser language (`Accept-Language`) | None | It is the visitor's language, not their location |

## Decision

C now, A when there is a reason. If the browser's first language is Spanish, the page is in Spanish; otherwise, English. The switch's choice is saved in `localStorage` and overrides both.

## Consequences

- No extra provider.
- A visitor in a Spanish-speaking country with an English browser sees English, which is the language they chose.
- The API decides the language in one function that already receives the country (empty for now), and `visit.country` exists, so adding A is a small change.
