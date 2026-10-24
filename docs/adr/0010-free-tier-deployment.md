# 0010 · Free-tier deployment

Status: accepted · Date: 2026-10-18 · Amended: 2026-10-20 (where backups go)

## Context

The site should run at no cost for now. The paid VPS with Docker Compose and Caddy ([ADR 0001](0001-vps-deployment-docker-compose.md)) and its staging server ([ADR 0008](0008-staging-environments.md)) stay as the target, so moving there later must be cheap. This ADR adds a free phase before them without changing either.

What the site needs from a host, as built:

- **One origin.** The session cookie is `SameSite=Strict` and the CSP only allows `connect-src 'self'`, so splitting the page and the API across domains would break the admin login. `/api` must stay under the page's domain.
- **Postgres 18** that doesn't expire and can be backed up with `pg_dump`.
- **Disk for `/media`**, where the API writes WebP screenshots.
- **Outbound SMTP on port 587** for the contact notice ([ADR 0005](0005-contact-notice-gmail-smtp.md)).
- **No long cold start** on the first visit.

## Free tiers checked on 2026-10-18

- **Render** ([docs](https://render.com/docs/free)): free web services sleep after 15 idle minutes and take about a minute to wake; no persistent disk; outbound ports 25, 465 and 587 are blocked ([changelog](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports)); free Postgres expires after 30 days.
- **Neon** ([limits](https://neon.com/faqs/free-plan-limits-and-quotas)): 1 GB and 100 CU-hours per project a month; compute suspends after 5 idle minutes and that can't be turned off.
- **Oracle Cloud Always Free** ([free tier](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm), [resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm)): up to two AMD `VM.Standard.E2.1.Micro` VMs (1/8 OCPU with bursting, 1 GB of memory), 200 GB of block storage and 10 TB of outbound data a month, in the home region. Port 25 is blocked; 587 isn't. Oracle may reclaim an instance that stays idle for 7 days.
- **Resend** ([pricing](https://resend.com/pricing.md)): 3,000 emails a month and 100 a day, over HTTPS.
- **Google Cloud** ([free features](https://docs.cloud.google.com/free/docs/free-cloud-features)): one e2-micro VM, but only 1 GB of outbound data a month and a paid external IPv4 address. Not free.
- **Fly.io and Koyeb:** no free web service for new accounts.

## Options considered

| Option | What it is | Monthly cost | Setup | Limits and risks |
|---|---|---|---|---|
| A. Oracle Always Free VM | One AMD micro VM running the same `compose.prod.yml`, Caddy and `deploy.sh` as ADR 0001. Production only; staging stays the CI `deploy-check` job | $0 (card on file) | ~6 h, reused on the paid VPS | Idle reclamation; slower screenshot processing on 1/8 OCPU; 1 GB of memory, within the 768 MiB the compose limits already target |
| B. Render + Neon + Resend | A static site rewriting `/api` to a free web service, Postgres on Neon, screenshots in Postgres and email over Resend's API | $0 | ~10 h of code that only exists for this host | A minute of cold start; three providers; changes ADR 0005 |
| C. The paid VPS now | ADR 0001 for production only | ~US$7.20 | ~6 h | Not free |

## Decision

A. It is the only free option that runs the site as built, with no code changes. Moving to the paid VPS later means changing the host in the deployment secrets and restoring a backup.

Its two risks are handled without new layers:

- **Idle reclamation:** a reclaimed VM is rebuilt with `deploy.sh` and a restore, so backups must leave the VM. *Amended 2026-10-20:* `backup.sh` encrypts each backup on the VM with age to a public key whose private key is kept offline, and uploads it to a private Object Storage bucket in the same account (20 GB free; reclamation applies only to compute, per the [Always Free resources page](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)). The VM uploads with its instance principal under a policy that only allows creating objects and listing their names, so there is no key on the server and a compromised server can't read or delete old backups. The bucket deletes them after 14 days, and a monthly copy is kept off Oracle in case the account closes. A GitHub Actions artifact was rejected: artifacts of a public repository can be downloaded by any signed-in GitHub user.
- **No capacity at signup:** fall back to C, not B, because B's changes would be thrown away.

## Consequences

- ADR 0001 and ADR 0008 remain the target. When the paid phase starts, this ADR is marked superseded.
- Production runs without a staging server or its release gate; every PR still runs the full production stack in `deploy-check`.
- A free subdomain with a Caddy certificate works until a custom domain is bought.
