# 0010 · Free deployment while job hunting

Status: accepted · Date: 2026-10-18 · Decided by: Nicolas · Amended: 2026-10-20 (where backups go)

## Context

Nicolas wants the portfolio online at no cost, at least while he is looking for a job. The planned deployment stays the long-term target: a DigitalOcean VPS (virtual private server) with Docker Compose and Caddy (ADR 0001, architecture decision record) plus staging (ADR 0008). Moving to it later must be cheap, so this ADR does not change either of them; it adds a temporary phase before them.

What the site needs from a host, as it is built today:

- **One origin.** Caddy serves the page, `/media` and `/api` on the same domain. The admin session cookie is `SameSite=strict` and the CSP (Content Security Policy) only allows `connect-src 'self'`, so splitting the page and the API across two domains (for example GitHub Pages plus an API elsewhere) breaks the admin login and needs CORS (cross-origin resource sharing) and security changes. Any option must keep `/api` under the page's domain.
- **Postgres 18** that does not expire and can be backed up with `pg_dump`.
- **Disk for `/media`:** project screenshots are WebP files written by the API.
- **Outbound SMTP (Simple Mail Transfer Protocol) on port 587** for the contact notice through Gmail (ADR 0005).
- **No long cold start:** a recruiter's first visit should not wait a minute (ADR 0001).

sunsapp was published at $0 on Render's free plan plus GitHub Pages (sunsapp ADR 0009). It works there because sunsapp has no database, no uploads, no email and no login.

## Checked on 2026-10-18 (official docs)

Free tiers change often; every limit below is what the provider's page said on this date.

- **Render** ([render.com/docs/free](https://render.com/docs/free)): free web services spin down after 15 minutes without inbound traffic and take about one minute to wake; 750 free instance hours per workspace per month; no persistent disk; **outbound traffic to ports 25, 465 and 587 is blocked** (since 2025-09-26, [changelog](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports)). Free Postgres has 1 GB, **expires 30 days after creation** and has no backups. A static site can rewrite a path to a full URL ([redirects-rewrites](https://render.com/docs/redirects-rewrites)), which would keep `/api` on the same origin.
- **Neon** ([free plan limits](https://neon.com/faqs/free-plan-limits-and-quotas)): 1 GB per project, 100 CU-hours (compute unit hours) per project per month, compute suspends after 5 minutes idle and that can't be turned off; the limits don't delete data.
- **Oracle Cloud Always Free** ([free tier](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm), [resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm)): up to two AMD `VM.Standard.E2.1.Micro` VMs (1/8 OCPU (Oracle CPU) with bursting, 1 GB of memory, x86), or Arm A1 up to 2 OCPU and 12 GB in total; 200 GB of block storage and five volume backups; 10 TB of outbound data per month. Always Free resources stay after the 30-day trial. Signup needs a phone number and a credit card, which is not charged unless the account is upgraded. Instances must be in the home region, chosen at signup (Santiago, Chile, is a region). Port 25 is blocked by default; the page does not restrict 587. **Oracle may reclaim an instance it deems idle for 7 days** (95th-percentile CPU under 20 % and network under 20 %; memory under 20 % too, A1 only). The page does not say whether this applies after upgrading to Pay As You Go, or whether Oracle warns first.
- **Resend** ([pricing](https://resend.com/pricing.md)): free plan with 3,000 emails a month and 100 a day, over an HTTPS API.
- **Google Cloud** ([free features](https://docs.cloud.google.com/free/docs/free-cloud-features), [network pricing](https://cloud.google.com/vpc/network-pricing?hl=en)): one e2-micro VM in a US region with 30 GB of disk, but only 1 GB of outbound data a month and the external IPv4 address costs US$0.005 an hour (about US$3.65 a month). Not $0, so it is left out.
- **Fly.io and Koyeb:** no free web service for new accounts (checked 2026-10-17 in sunsapp ADR 0009). Left out.

## Options considered

| Option | What it is | Monthly cost | Extra work | Limits and risks |
|---|---|---|---|---|
| **A. Oracle Always Free VM** | One AMD micro VM in the home region running the same `deploy/compose.prod.yml`, Caddy and `deploy.sh` as ADR 0001. Production only; staging stays the CI (continuous integration) `deploy-check`. | $0 (credit card on file) | ~6 h, the same as tasks 5.2 to 5.4 for production, and it carries over to DigitalOcean | Idle reclamation; 1/8 OCPU makes screenshot uploads slower; 1 GB of memory, the same budget the compose limits already target (768 MiB); a provider account with a card |
| B. Render free + Neon + Resend | Render static site with a rewrite of `/api/*` to a free Render web service; Postgres on Neon; screenshots stored in Postgres instead of `/media`; the contact notice sent through Resend's HTTPS API instead of SMTP | $0 (no card at Render or Neon) | ~10 h: new storage for screenshots (an add-only migration plus a route), a new mail provider in `mail.py` (changes ADR 0005), the visitor IP behind Render's proxy for the rate limit, `render.yaml` | About one minute of cold start after 15 idle minutes, plus Neon waking up; three providers; most of the code changes only exist for this host |
| C. Bring the planned VPS forward | Milestone 5 for production only on DigitalOcean (ADR 0001), without the staging VPS from ADR 0008 for now | ~US$7.20 | ~6 h | It is not free |

The .cl domain (CLP 9,990 a year, plan task 5.1) is optional with A and C: Caddy can get a certificate for a free subdomain (for example DuckDNS) until the domain is bought. With B the site lives on `*.onrender.com`.

## Decision

**A: Oracle Always Free VM** (Nicolas, 2026-10-18). It is the only $0 option that runs the site as it is built, with no code changes: one origin, Postgres with `pg_dump`, a real disk for `/media`, SMTP on 587 and no cold start. The work is the one milestone 5 already plans, so moving to DigitalOcean later means changing the host in `deploy.yml`'s secrets and restoring a backup.

The two risks and how to handle them, without adding layers:

- **Idle reclamation:** the daily `pg_dump` and `/media` copy (task 5.4) must leave the VM, so a reclaimed VM is rebuilt with `deploy.sh` and a restore. **Amended on 2026-10-20 (Nicolas):** the backup is encrypted on the VM with age to a public key whose private key only Nicolas holds, and it is uploaded to a private Object Storage bucket in the same Oracle account (20 GB in Always Free; the idle reclamation applies only to compute instances, per the [Always Free resources page](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), checked on 2026-10-20). The VM uploads with its instance principal and a policy that only allows creating objects and listing their names, so there is no key on the server and a compromised server can't read or delete old backups; the bucket deletes them after 14 days, and Nicolas keeps a monthly copy on his machine in case the account closes. The first idea, a GitHub Actions artifact, was dropped: the repo is public and any signed-in GitHub user can download its artifacts, so even an encrypted backup would sit in public view. Upgrading to Pay As You Go is reported to stop reclamation, but the official page does not say so; check before relying on it, and set a budget alert at US$1 if the account is upgraded.
- **Capacity at signup:** if no micro VM can be created in the home region, fall back to C rather than B, because B's changes are throwaway work.

B is worth it only if a credit card at Oracle is a no-go. C is the fallback when $0 stops being the priority.

## Consequences

- ADR 0001 and ADR 0008 stay as the target; this phase ends when Nicolas decides to pay for the VPS, and then this ADR is marked superseded.
- The plan gets a free production phase in milestone 5 (tasks 5.2 to 5.4 against the Oracle VM, without the staging server and its release gate); the plan is updated only after this ADR is accepted.
- Nicolas creates the Oracle account and the VM himself (it needs his card); no deployment or secret is created before that.
