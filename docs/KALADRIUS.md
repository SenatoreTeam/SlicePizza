# What we can learn from Kaladrius

[Kaladrius](https://github.com/facchini-miguel/kaladrius) (Miguel's clinic management system, Django, version 0.72.2 when this was written, 2026-11-20) is the same kind of project as SlicePizza in one way that matters: a small team, real data, a public repository, documentation in several languages, releases by pipeline, and a production on a VPS with Dokploy, **the same server** (see its [reference production](https://kaladrius-docs.facchini.eti.br/project/production)). The domains differ (health records and money versus pizza orders), so this is about **how it is run**, not what it does.

Each row says what Kaladrius does, what SlicePizza has today, and what we decided. The result is the plan in the [roadmap](ROADMAP.md#after-phase-8-the-next-stage).

## What we already do the same way

| Practice | Kaladrius | SlicePizza |
|---|---|---|
| A decision log, with dates and reasons | A table of 214 numbered decisions | [ADRs](adr/README.md), one file each (0001 to 0021) |
| Versions in a file, release by pipeline | `releases.yaml`, a `release` job | `releases.toml`, the pipeline's `release` job |
| Dependabot with a 7-day wait | 7-day cooldown, grouped by kind | 7-day cooldown, each package alone |
| Lock files with hashes, checked in CI | `deploy/lock.sh --check` | `compile-requirements.sh`, the `lock-files` job |
| Docs site in two or more languages | English, Portuguese, Spanish | English, Portuguese |
| `main` only through a reviewed PR | Ruleset "Protect main" | Ruleset "Protect main" |
| Secrets out of Git, security headers, lockout | Argon2, lockout, CSP, audit log | Gitleaks, Trivy, rate limit, [SECRETS.md](SECRETS.md) |
| Behind the server's own proxy and monitoring | Traefik, Healthchecks.io, Prometheus files | The same server ([ADR 0016](adr/0016-server-monitoring.md)) |

## What Kaladrius has and we do not

| Kaladrius | Why it matters for us | Decision |
|---|---|---|
| **A privacy policy, retention and anonymization** (a written LGPD policy, a retention command, an anonymization command, data-subject requests) | We store customers' names, phones, addresses and Telegram chat ids **forever**, and have no policy. Customers can ask what we keep | **Adopt**: Phase 9 |
| **Database migrations, and a report of them on every PR** (SQL each one runs, destructive operations, a back-and-forth test) | We still create tables with `create_all` ([ADR 0002](adr/0002-sqlalchemy-and-schema-creation.md)): a column added later never reaches the server's database. Every schema change is a risk until this exists | **Adopt**: Phase 10 |
| **Test coverage measured, with a minimum (90%)** | We do not measure it, so it can fall unnoticed | **Adopt**: Phase 10, starting at today's number |
| **Actions pinned by commit, base images pinned by digest** | A moved tag (`@v7`, `python:3.15-slim`) changes what we run without a PR. 28 workflow steps and every base image use tags | **Adopt**: Phase 11 |
| **`CODEOWNERS`: who must approve what** | Today any teammate's approval is enough for anything. Structural files (CI, Docker, deploy, schema, access) deserve a named owner | **Adopt**: Phase 11, the owners agreed together |
| **SECURITY.md, CODE_OF_CONDUCT.md, issue templates** | The repository is public: people need to know how to report a vulnerability and where to ask | **Adopt**: Phase 11 |
| **Dependabot groups** (tools, minor updates, docs) | Fewer, bigger PRs to review than one per package | **Adopt**: Phase 11 |
| **Login protection: lockout after wrong passwords, optional two-step, 30-minute sessions** | Our kitchen login is Caddy's basic auth: no attempt limit ([SECRETS.md](SECRETS.md#review-phase-8-2026-11-19)) | **Adopt** (lockout first): Phase 11 |
| **`X-Robots-Tag: noindex`** on the system (so only the website and docs are found) | The API and the kitchen should never be search results | **Adopt**: Phase 11, a small change |
| **Operations docs**: backup and restore, monitoring, upgrade, with exact commands and who does what | We have DEPLOY.md but no runbook for "it broke at 7 p.m. Friday" | **Adopt**: Phase 12 |
| **A glossary, a FAQ, a quick start, a user manual per role** | New people (and Zé) need a way in that is not the code | **Adopt**: Phase 12 |
| **A public demo with logins per role, reset every night** | Lets anyone try the kitchen and the menu without asking | **Maybe**: Phase 12, if Miguel agrees to host it |
| **Automatic rollback of the server's update** (the new version must answer `/health`, else the old one comes back) | Our DEPLOY.md says the server checks and goes back; it is Miguel's script, and we have never tested it by breaking a version on purpose | **Check together**: Phase 12 |
| **Server numbers for Prometheus** (backup age, restore test, update result) | The server already watches SlicePizza from outside ([ADR 0016](adr/0016-server-monitoring.md)); we could ask for the same signals for our containers | **Ask**: Phase 12 |
| **A weekly restore test** of the newest backup into a throwaway database | Backups are the server's ([ADR 0018](adr/0018-server-backups.md)), but nobody has restored SlicePizza's data from them | **Ask**: Phase 12 |

## What we leave out on purpose

| Kaladrius | Why not |
|---|---|
| `.deb`, `.rpm` and Arch packages, an apt repository | SlicePizza has one real installation, not many clinics installing it themselves |
| A mobile app (React Native) | The menu site works on a phone; no request for an app |
| Multi-tenant (one install, many clinics) | One pizzeria |
| Roles with permission matrix, two-step for staff, an audit log of every record view | We have two roles (customers, the kitchen); revisit if the kitchen grows to several people with different powers |
| A third language (Spanish) | The users speak Portuguese; English is for the team and the portfolio |
| Brand kit, funding file | Not needed now |

## What Kaladrius could take from us

Worth telling Miguel, since it is his server and his project too: Trivy scanning every image **before** publishing, Gitleaks over the whole history, `SECRETS.md` (an inventory of credentials with how to rotate each), the rate limit on the route that costs people attention, and the k6 load test.
