# Roadmap

Each phase starts with a **request from Zé**, the pizzeria owner. The request is the problem; the tasks are the solution; the **definition of done** tells you when the phase is over.

Check the boxes as you make progress, and keep each phase's **Status** line in step with the roadmap table in the [README](../README.md#roadmap): ✅ Done, 🚧 In progress, ⏸ Postponed, 📝 Proposed or ⏳ Not started.

---

## Phase 1: "I want to see it running on your computer"

**Status:** ✅ Done

**Goal:** the orders API running locally, in containers, saving to the database.

- [x] Initial repository structure and documentation
- [x] API with `GET /health` and `GET /menu` (menu hardcoded, to start)
- [x] First automated test with pytest
- [x] Dockerfile for the API
- [x] `docker-compose.yml` with API + Postgres
- [x] `.env.example` with the database variables (the real `.env` never goes into Git)
- [x] Connect the API to Postgres (suggestion: SQLAlchemy or psycopg)
- [x] Create the `pizzas` and `orders` tables
- [x] Move the menu into the database
- [x] `POST /orders`: create an order
- [x] `GET /orders/{id}`: get an order
- [x] `PATCH /orders/{id}/status`: change the status (`received` → `preparing` → `out_for_delivery` → `delivered`)
- [x] Tests for the new routes

**Done when:** `docker compose up` brings everything up from scratch, and an order you created is still saved after `docker compose down` + `docker compose up`.

**You learn:** Python, SQL, Git, Docker, volumes and container networking.

---

## Phase 2: "I want the site live on my own domain"

**Status:** ✅ Done: live at https://slicepizza.senatore.tech since 2026-11-15

**Goal:** the system reachable from the internet, over HTTPS, on your domain.

- [x] Register a domain (e.g. Registro.br, Cloudflare or Namecheap)
- [x] Create a cloud virtual machine (AWS EC2 or Oracle Cloud Free Tier): a shared server that already existed
- [x] Set up SSH access with a key (no password): the shared server's own setup
- [x] Open only ports 22, 80 and 443 in the firewall: the shared server's own setup
- [x] Install Docker on the virtual machine
- [x] Build the menu website in `frontend/` (plain HTML + JS)
- [x] Host the static site on a CDN (Cloudflare Pages or S3 + CloudFront): served by the Caddy container instead, see below
- [x] DNS: `www` (CNAME to the CDN), `api` and `admin` (A record to the virtual machine): one record for `slicepizza.senatore.tech`, see below
- [x] Caddy as reverse proxy, with automatic HTTPS: Caddy routes, the server's proxy does the HTTPS

> **How SlicePizza did it:** the system lives at `slicepizza.senatore.tech` on a shared server that already has a domain, Docker and an HTTPS proxy (Dokploy, see [DEPLOY.md](DEPLOY.md)). Instead of a CDN plus `api` and `admin` subdomains, a Caddy container serves the site at `/` and the API at `/api` on that one domain ([ADR 0003](adr/0003-one-domain-caddy-in-front.md)). The server's proxy keeps the HTTPS part.

**Done when:** you place an order from your phone, over HTTPS, through the internet.

**You learn:** DNS, SSH, firewalls, reverse proxies, TLS and CDNs.

---

## Phase 3: "Customers want to know when their pizza is on the way"

**Status:** ✅ Done: live at https://slicepizza.senatore.tech since 2026-11-15 (the Telegram bot, RabbitMQ and the worker run on the server, and an order on a phone was followed on Telegram end to end)

**Goal:** notify the customer on every status change, without slowing down the API.

- [x] Add RabbitMQ to `docker-compose.yml`
- [x] The API publishes an event to the queue when an order's status changes (through an outbox, [ADR 0004](adr/0004-order-events-outbox-rabbitmq.md))
- [x] Create the worker in `worker/` that consumes the queue ([ADR 0005](adr/0005-notification-worker.md))
- [x] Create a Telegram bot and send the notification from the worker: to the pizzeria chat, and to customers who tap "Follow on Telegram" on their order page ([ADR 0006](adr/0006-customer-telegram-opt-in.md))
- [x] Build the kitchen dashboard: the kitchen board at `/kitchen`, behind a login; changing a status is now the kitchen's only ([ADR 0007](adr/0007-kitchen-login.md))

**Done when:** if you take the worker down, messages wait in the queue and are sent when it comes back.

**You learn:** asynchronous systems, queues and services talking to each other.

---

## Phase 4: "Every time you change something, something breaks"

**Status:** ✅ Done: live since 2026-11-17. A merge that adds a version to `releases.toml` reaches production by itself, checked, without anyone logging into the server (versions 1.0.0 and 1.1.0 went out this way)

**Goal:** all code goes through automated tests before reaching production.

- [x] GitHub Actions pipeline: lint → tests → image build: one pipeline, where the images wait for the lint and every test ([ADR 0008](adr/0008-one-gated-pipeline.md))
- [x] Publish images to GHCR (GitHub's container registry): from `main` only, and only when the pipeline passed, as `sha-<commit>`; a merge that adds a version to `releases.toml` also tags them with it and creates the release ([ADR 0009](adr/0009-numbered-versions.md), [ADR 0010](adr/0010-releases-file.md))
- [x] Automatic deploy to the virtual machine after merging into `main`: when the merge adds a version, the server fetches it from GHCR, backs up the database, deploys it and checks it, and puts the previous version back if the checks fail ([ADR 0009](adr/0009-numbered-versions.md)). The version and what changed show in the system ([Versions and releases](https://slicepizza-docs.senatore.tech/docs/phase-4/versions))
- [x] ~~Staging environment at `staging.yourdomain.com`~~ Not used (decided 2026-11-17): each version goes straight to production, where the server checks it and puts the previous version back by itself if the checks fail. A copy of the system for testing (QA) would cost a second set of containers, data and secrets on the shared server for little gain at this size
- [x] ~~Secrets stored in GitHub Secrets~~ Not needed: the deploy keeps no secret on GitHub. The server fetches the public images itself, and the system's own secrets stay on the server ([ADR 0009](adr/0009-numbered-versions.md))

**Done when:** a merge into `main` puts the new version in production without you logging into the server.

**You learn:** CI/CD, separate environments, secrets and image versioning.

---

## Phase 5: "The site went down Friday night and nobody noticed"

**Status:** ✅ Done (2026-11-19)

**Goal:** know something broke before a customer complains.

- [x] `/health` route on every service (each container has a health check; the API's `/health` is the full-path one)
- [x] ~~Expose API metrics to Prometheus: orders, latency, errors and the outbox backlog at `/metrics`, private ([ADR 0012](adr/0012-api-metrics.md))~~ Removed with [ADR 0016](adr/0016-server-monitoring.md) (version 1.2.1): this repository implements no monitoring, the server's monitoring watches the system
- [x] ~~Grafana dashboards: the SlicePizza overview, provisioned from Git ([ADR 0013](adr/0013-prometheus-and-grafana.md))~~ Replaced (decided 2026-11-19, [ADR 0016](adr/0016-server-monitoring.md)): the server's own monitoring, shared by every project on it, already shows SlicePizza's containers, queue, outbox, orders, backups, version and sites. For now it has general panels only, none for one service
- [x] ~~Centralize container logs in Loki, collected by Alloy through a read-only Docker proxy, 7 days, shown in Grafana ([ADR 0014](adr/0014-loki-and-alloy.md))~~ Removed with [ADR 0016](adr/0016-server-monitoring.md): monitoring belongs to the server, not to this repository
- [x] ~~Telegram alerts from Grafana: API down, 5xx, stuck outbox, queue backlog, error logs ([ADR 0015](adr/0015-grafana-telegram-alerts.md))~~ Removed with [ADR 0016](adr/0016-server-monitoring.md): alerts, like the dashboards, belong to the server's monitoring

- [x] ~~External uptime check~~ Not needed: the server's own monitoring already watches `/api/health` and the public sites ([ADR 0016](adr/0016-server-monitoring.md))

**Done when:** someone is told when SlicePizza breaks. That is the server's monitoring, not this repository ([ADR 0016](adr/0016-server-monitoring.md)); this repository keeps the health checks. (The down-on-purpose test passed locally, 56 s, with the former alerts of ADR 0015.)

**You learn:** health checks, and why on a shared server the monitoring belongs to the server ([ADR 0016](adr/0016-server-monitoring.md)).

---

## Phase 6: "The server died and we lost the orders"

**Status:** ✅ Done (2026-11-19), by the server's owner, not by this repository ([ADR 0018](adr/0018-server-backups.md))

**Goal:** be able to rebuild everything from scratch, with the data, quickly.

The whole VPS is backed up by the server's owner, Postgres and RabbitMQ volumes included, the same way monitoring is the server's job ([ADR 0016](adr/0016-server-monitoring.md)). Nothing for this repository to build.

- [x] ~~Daily encrypted Postgres backup, offsite copy, retention~~ Covered by the backup of the whole VPS (server owner)
- [x] ~~Restore test and rebuild runbook~~ Restoring is done from the VPS backup (server owner). The rebuild steps that belong to SlicePizza are in [`DEPLOY.md`](DEPLOY.md): the compose file and `.env.example` are in Git
- [x] ~~Terraform and Ansible~~ Not used: Docker and Dokploy on a VPS ([ADR 0017](adr/0017-docker-only-infrastructure.md))

**Done when:** the server's owner can bring the VPS back, with the data, from its backup. This repository only has to stay reproducible from Git.

**You learn:** why backups and disaster recovery sit at the layer that owns the disk, and what the application must keep reproducible (config in Git, secrets in `.env`).

---

## Phase 7: "We're running a R$20 pizza promo on Friday"

**Status:** ✅ Done (2026-11-19); two items need the server's owner (a `redis` container, the number of API copies)

**Goal:** handle much more traffic without going down, on the same VPS and with the same Docker setup ([ADR 0017](adr/0017-docker-only-infrastructure.md)).

- [x] Load test with k6 to find the bottleneck: [`infra/loadtest/`](../infra/loadtest/) (baseline: 570 requests/s, p95 146 ms in stress mode on one machine, no errors)
- [x] Cache the menu in Redis, optional and fail-safe ([ADR 0019](adr/0019-redis-menu-cache.md)): 570 → 866 requests/s in stress mode; **needs a `redis` container on the server**
- [x] Run several copies of the API behind Caddy (Docker replicas), with resource limits per container ([ADR 0020](adr/0020-api-replicas.md)): 708 → 1212 → 1572 requests/s with 1, 2, 4 copies; **the number of copies is set on the server**
- [x] Database: explicit, tunable connection pool per copy, and the index question answered with "not needed at this size" (see ADR 0020)
- [x] Capacity notes: how far one VPS goes and what the next step is ([`infra/loadtest/README.md`](../infra/loadtest/README.md#capacity-notes-phase-7))
- [x] ~~Pizza photos through the CDN~~ Not applicable yet: the menu has no photos. When it does, serve them from the site with long cache headers behind Cloudflare, with file names that change when the picture does

**Done when:** the system handles 10 times the normal traffic without errors. It does, with one API copy and no cache: the other items make it faster and more available.

**You learn:** scalability, caching, horizontal scaling with containers and load testing. (Kubernetes is out of scope on one VPS: see [ADR 0017](adr/0017-docker-only-infrastructure.md).)

---

## Phase 8 (bonus): "I heard hackers attack pizzerias"

**Status:** ✅ Done and released in 1.4.0 (2026-11-19) ([ADR 0021](adr/0021-hardening.md))

**Goal:** close the most obvious doors.

- [x] Passwords and keys kept out of Git: `.env` is ignored, the whole history is scanned by Gitleaks on every change, and [`docs/SECRETS.md`](SECRETS.md) lists every credential with its rotation routine
- [x] Scan images for vulnerabilities with Trivy in the pipeline, before anything is published; first findings fixed (pip removed from the images, zlib1g, Caddy 2.11.9), two in Caddy accepted with an expiry date
- [x] Limit requests per client on the API: 30 orders per minute per address, 429 with `Retry-After`
- [x] Containers running as a non-root user: `api`, `worker`, `web` and now `redis`; Postgres and RabbitMQ drop to their own user after fixing their folders (how the official images work)
- [x] Review the permissions of every token and credential: [`docs/SECRETS.md`](SECRETS.md#review-phase-8-2026-11-19). The server-side items (SSH, Dokploy, Cloudflare, backups) are for the server's owner to confirm

**You learn:** the basics of DevSecOps.

---

# After Phase 8: the next stage

**Status:** 📝 Proposed (2026-11-20), to be agreed by Ettore and Miguel. Built from a comparison with [Kaladrius](https://github.com/facchini-miguel/kaladrius): [what we learned and what we left out](KALADRIUS.md).

Phases 1 to 8 built the system. This stage is about **running it responsibly**: what we do with customers' data, changing the database safely, trusting what we run, and being able to handle a bad evening. Nothing here adds a feature a customer sees, except a privacy page.

## How we organize

- **Two people, two areas.** Ettore: the application, the pipeline and the docs. Miguel: the server, Dokploy and what runs there. The **Owner** column below is a proposal; changing it is a conversation, not a rule.
- **One issue per task**, with the label `phase-9` to `phase-12` and the task's id (for example `9.2`), opened when the task starts. A task that needs the server gets its own issue for Miguel (server steps go in issues for him, with the exact steps), with the exact steps.
- **Size:** S is under an hour, M is a session, L is several PRs. **Depends** says what must come first.
- **Order:** within a phase, top to bottom. Between phases: 9 and 10 first (they protect customers and the database), then 11, then 12. 11 and 12 can interleave.
- **Every task ends the same way:** tests, docs in English **and** pt-BR, an ADR when it is a decision, then a PR, a review and a merge. A task that changes what runs in production is released as a version.
- **Check the boxes here** as tasks finish, and keep the README's table in step.

## Phase 9: "A customer asked what you do with her phone number"

**Status:** 🚧 In progress (started 2026-11-21; 9.1, 9.3, 9.4, 9.6, 9.7 live in 1.5.0; 9.2 and 9.5 wait for a lawyer check and for Miguel). Issues: [#77](https://github.com/SenatoreTeam/SlicePizza/issues/77) to [#82](https://github.com/SenatoreTeam/SlicePizza/issues/82). The data map ([`.lgpd/`](../.lgpd/data-map.en.md)) is done and found two more tasks: 9.6 and 9.7.

**Goal:** know what personal data we keep, keep it only as long as needed, and say it in plain words (LGPD). Use the project's LGPD sources (`goul4rt/lgpd-skills`, `ctresb/leis`).

| Id | Task | Owner | Size | Depends |
|---|---|---|---|---|
| 9.1 ✅ | **Map the data** ([#77](https://github.com/SenatoreTeam/SlicePizza/issues/77)): what we keep (customer name, phone, address, order items, the Telegram chat id of customers who follow an order), where (Postgres, RabbitMQ messages, the worker's log, the server's logs and backups), who sees it, why | Ettore | S | |
| 9.2 📝 | **Privacy policy** ([#78](https://github.com/SenatoreTeam/SlicePizza/issues/78)): **draft written** in [`.lgpd/`](../.lgpd/privacy-policy.en.md) (EN + pt-BR), **not published**: it waits for the lawyer/encarregado check, Miguel's answers ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)) and the real pizzeria details. Original text: in English and pt-BR: controller (the pizzeria), what, why, legal basis, retention, rights and how to use them, the contact. A page on the menu site, linked from the order form | Ettore | M | 9.1 |
| 9.3 ✅ | **Retention** ([#79](https://github.com/SenatoreTeam/SlicePizza/issues/79), [ADR 0023](adr/0023-retention-of-personal-data.md)): decided 12 months for finished orders and 7 days for chat links; built into the API, nothing to schedule on the server. **Live since 1.5.0 (2026-11-21)**. Original text: decide how long an order's personal data is kept (proposal: 12 months, then name, phone and address are replaced, the order and its total stay for the numbers); a job that does it; the Telegram chat link removed when the order is finished and old | Ettore | L | 9.1, an ADR |
| 9.4 ✅ | **A customer's request** ([#80](https://github.com/SenatoreTeam/SlicePizza/issues/80), [runbook](PRIVACY-REQUESTS.md)): command `python -m app.dsar export/erase`, runbook in EN + pt-BR, reply templates. **Live since 1.5.0 (2026-11-21)**. Original text: (see my data, delete my data): the steps for the pizzeria, as a runbook and a command | Ettore | M | 9.3 |
| 9.5 | **Logs and backups** ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)): confirm the worker and the proxy do not log phone numbers or addresses; ask how long the server keeps logs and backups, so the policy tells the truth | Miguel | S | 9.1 |
| 9.6 ✅ | **Self-host the fonts** ([#82](https://github.com/SenatoreTeam/SlicePizza/issues/82)): the pages send every visitor's IP to Google Fonts; serve them from our domain and tighten the Content-Security-Policy. Done and **live since 1.5.0 (2026-11-21)** | Ettore | S | |
| 9.7 ✅ | **Minimize the order link** ([#83](https://github.com/SenatoreTeam/SlicePizza/issues/83), [ADR 0022](adr/0022-order-link-without-personal-data.md)): `GET /orders/<id>` shows name, phone and address to anyone with the link; show items and status only (the kitchen keeps the full view). Done and **live since 1.5.0 (2026-11-21)** (with 9.6) | Ettore | M | 9.1 |

**Done when:** the policy is live on the site, orders older than the retention period no longer hold a name, a phone or an address, and a request from a customer can be answered in a day.

## Phase 10: "We changed the database and it hurt"

**Status:** 🚧 In progress (10.4 done)

**Goal:** change the schema without losing orders, and know the tests cover what matters.

| Id | Task | Owner | Size | Depends |
|---|---|---|---|---|
| 10.1 | **Migrations with Alembic**: a first migration that matches today's tables, so the server's database is "at version 1"; `create_all` stops being the way ([ADR 0002](adr/0002-sqlalchemy-and-schema-creation.md)). Applied when the API starts | Ettore | L | an ADR; the server's database is checked first |
| 10.2 | **A migration report on every PR that touches one**: the SQL, the operations that delete data, a test that goes up and back down on Postgres (Kaladrius: decision 139) | Ettore | M | 10.1 |
| 10.3 | **A rule for the rollback**: the pipeline's automatic rollback puts the old image back but never undoes a migration, so migrations must work with the previous version (add, never rename, in one step). Written in `CONTRIBUTING.md` | Ettore | S | 10.1 |
| 10.4 | ✅ **Measure coverage** in the pipeline and fail below today's number; raise it as tests are added. Done: `pytest --cov` in CI, API floor 85% (87% today), worker 70% (see [api/README.md](../api/README.md#test-coverage)) | Ettore | S | |
| 10.5 | **Tell Miguel** what the server must know: the API now migrates on start, so a restore of an old backup is migrated forward | Miguel | S | 10.1 |

**Done when:** a new column can be added in a PR, the PR shows its SQL, and the server's database gets it on release with no manual step.

## Phase 11: "How do I know nobody tampered with what we run?"

**Status:** 🚧 In progress (started 2026-11-21): 11.1, 11.2, 11.3, 11.5, 11.6 done; 11.4, 11.7, 11.8, 11.9 open

**Goal:** make sure only the code we reviewed, and the versions we chose, run in production, and that the repository is a good public citizen.

| Id | Task | Owner | Size | Depends |
|---|---|---|---|---|
| 11.1 ✅ | **Pin every GitHub Action by commit** (with the version in a comment), and let Dependabot update them | Ettore | S | |
| 11.2 ✅ | **Pin every base image by digest** (`@sha256`): `python`, `caddy`, `postgres`, `rabbitmq`, `redis`; Dependabot proposes the new digests | Ettore | M | |
| 11.3 ✅ | **Dependabot groups**: tools, minor updates, docs; limit open PRs (already in place since Phase 4; checked) | Ettore | S | |
| 11.4 | **`CODEOWNERS`**: structural files (`.github/`, Dockerfiles, `docker-compose.yml`, `infra/`, the schema and migrations, `api/app/auth.py`, `ratelimit.py`) need their owner's approval; the rest, any teammate | both | S | agree the list |
| 11.5 ✅ | (**needs the repository's *private vulnerability reporting* turned on in Settings → Security, by a repo admin; it is off today**) **`SECURITY.md`** (how to report privately through GitHub's advisories, what is supported, the answer time), **`CODE_OF_CONDUCT.md`**, issue templates (bug, idea) | Ettore | S | |
| 11.6 ✅ | **`X-Robots-Tag: noindex`** on the API and the kitchen; the site and docs stay indexable | Ettore | S | |
| 11.7 | **Kitchen login protection**: a lockout after wrong passwords (the login moves from Caddy's basic auth into the API or a small login page), a shorter session. An ADR first: this changes how the kitchen logs in | Ettore | L | an ADR |
| 11.8 | **Confirm the server items** listed as "not verified" in [SECRETS.md](SECRETS.md): SSH keys, Dokploy and Cloudflare two-step, `.env` permissions, who can read backups. Note the date | Miguel | S | |
| 11.9 | **Rotate the secrets once**, to prove the routine in SECRETS.md works, and fix the doc where it did not | both | M | 11.8 |

**Done when:** every workflow step and image is pinned, a vulnerability report has a place to go, and the kitchen's login stops a password-guessing script.

## Phase 12: "It broke at 7 p.m. on Friday"

**Status:** ⏳ Not started

**Goal:** anyone on the team can handle a bad evening, and a new person can start in an hour.

| Id | Task | Owner | Size | Depends |
|---|---|---|---|---|
| 12.1 | **Break a version on purpose** (a release whose `/health` fails) and watch the server put the old one back; write down what happened and how long it took | Miguel + Ettore | M | |
| 12.2 | **Restore test with SlicePizza's data**: restore the newest VPS backup into a throwaway place and check the orders are there; ask for it to repeat on a schedule | Miguel | M | |
| 12.3 | **Operations docs** (`docs/operations/`, EN + pt-BR): the upgrade and rollback steps, the restore, who to call, "the kitchen cannot see orders", "orders are not reaching Telegram", "the site is slow" (what to look at, in order) | Ettore | L | 12.1, 12.2 |
| 12.4 | **Ask what the server's monitoring watches for SlicePizza**, and ask for what is missing: the oldest unpublished event (the outbox) and the queue, an alert when `/api/health` fails | Miguel | S | |
| 12.5 | **A `/health` that tells about the outbox** (the age of the oldest unpublished event), so any monitor, ours or the server's, can see a stuck queue | Ettore | M | |
| 12.6 | **Docs for people**: a quick start, a glossary, a FAQ, and a short pt-BR manual for the kitchen (the people who use it) | Ettore | L | |
| 12.7 | **Maybe: a public demo** of the menu and the kitchen with a demo login, reset every night, as Kaladrius has. Needs Miguel to host it | both | L | agree first |

**Done when:** a failed release was rolled back on purpose and timed, a restore of SlicePizza's data was proven, and the runbooks answer the three evenings above.

## Parked

Not planned, with the reason in [the comparison](KALADRIUS.md#what-we-leave-out-on-purpose): installable packages, a mobile app, multi-tenant, a roles matrix and per-record audit, a third language. Revisit if the project changes shape.

## Ideas to decide before they become tasks

- **Version the API in the URL** (`/api/v1/...`, as Kaladrius does) now, while only our own site calls it? Cheap today, costly after other clients exist.
- **Who is the "controller"** in the privacy policy: Zé's pizzeria is fictional. For a real deployment the policy names the real business. Decide how the project's copy is worded (a template with placeholders).
- **A third reviewer**: with two people, every PR needs the other's time. If one is away, `--admin` is the way out; do we want a written rule for it?
