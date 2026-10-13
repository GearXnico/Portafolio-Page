# Brief · Portfolio website

ID: 2026-10-08-sitio-portafolio · Activated: 2026-10-11

## Problem

Nicolas wants to show his work as a full stack developer, Python backend developer and AI (artificial intelligence) developer, both to hiring teams and to project clients. Today he has no place where an evaluator can see, in one minute, what he can do, what he has built and how to contact him. GitHub shows the code, but it does not show the games or apps well, nor the architecture decisions.

The job postings reviewed do not require a portfolio. They do ask for React+TS (TypeScript), a Python API (application programming interface), SQL, tests, Docker, CI/CD (continuous integration and continuous deployment) and deployment. That is why the page is worth two things: what it shows and how it is built.

## Users and their main tasks

| User | Task | What they need to see or do |
|---|---|---|
| Recruiter or tech lead (arrives from a job application) | Decide in 1-2 minutes whether an interview is worth it | Profile, stack, experience and projects with a demo, all on one page and in their language |
| Referred client (a small business that arrives through a recommendation) | Check that Nicolas is trustworthy and write to him | Services, a written case study and a contact form |
| Nicolas (administrator) | Keep the portfolio up to date without touching code, and know which application or referral brought visits | A simple admin panel; visits and contacts per link |

## MVP (minimum viable product) scope (version 1)

1. A single page with a profile (text, no photo), skills, experience and contact.
2. **Spanish and English based on the visitor's location**, with a selector to switch language by hand. All editable content exists in both languages.
3. A projects section served by the API. The first case study is the page itself: architecture, pipeline, and what the AI did and what Nicolas decided.
4. **Admin panel** with a single user (Nicolas), protected with a password. It lets him create, edit, order and hide projects (title, description in both languages, stack, demo and repository links, screenshots) and edit the profile, skills and experience. It also shows contact messages and visits per link. The goal is that adding a project takes less than 10 minutes.
5. A contact form that saves the message and notifies Nicolas by email.
6. Links with UTM (Urchin Tracking Module) parameters per job application and per referral. A UTM is a parameter added to the end of a link to know where the visit comes from, for example `?utm_source=portal&utm_campaign=empresa-x`. This way each application or referral has its own link, and the site records how many visits and contacts each one brought.
7. A complete technical piece: React+TS frontend, FastAPI API, Postgres, tests (pytest and frontend), Docker and GitHub Actions that tests and deploys on every merge.
8. ~~The repository template stays separate and reusable for the next product.~~ Removed from this MVP (Nicolas, 2026-10-12): the template is done later as a separate project (`Product-template`), extracted from the finished portfolio.

## Outside the MVP

- Blog and rich text editor: descriptions are plain text or Markdown.
- More than one administrator user, or roles.
- Video or photo of Nicolas (rule of not being a public face).
- Embedded games or apps: they are added from the panel when they exist, as a link with a screenshot.
- The software factory agents (issue → PR). Only the template is made.
- A custom domain, if it complicates the first week's deployment: the site can be published first on the hosting subdomain.

## Estimated development time

Estimate at 40 h per week. It assumes Claude Code writes a large part of the code and that React and deployment take more time than the rest, because they are your weakest areas.

| Block | Hours |
|---|---|
| Repository template: structure, Docker, tests and CI/CD deploying an empty page | 14 |
| API and database: projects, profile, contact and visits by UTM | 14 |
| Public frontend: page, projects section and languages based on location | 18 |
| Admin panel: login and editing of projects, profile and messages | 18 |
| Content in two languages and the case study of the page itself | 8 |
| Final testing, adjustments and launch | 8 |
| **Total** | **80 h (about 2 weeks)** |

Range: between 65 h (optimistic) and 110 h (pessimistic, if deployment or the panel get complicated). Target date for version 1: **2026-10-25**; in the pessimistic scenario, 2026-10-30.

## Success metrics

For the portfolio as a product:

- **More than 1 new development added to the portfolio in less than 1 month after launch.**
- Visits from 5 or more job applications in the first 8 weeks.
- At least one interview where it is mentioned, or one contact from a client through the form.

Technical, for version 1:

- Automatic deployment on every merge to the main branch, with green tests in CI.
- Adding a project from the panel takes less than 10 minutes.
- ~~The template lets the next product start in 1 day or less.~~ Moved to the template project (2026-10-12).

## Abandonment criterion

Not applicable. It is his own portfolio and is maintained over time (Nicolas's decision, 2026-10-11).

## Assumptions to confirm

- No photo.
- The form notifies by email.
