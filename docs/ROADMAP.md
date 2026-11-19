# Roadmap

Each phase starts with a **request from Zé**, the pizzeria owner. The request is the problem; the tasks are the solution; the **definition of done** tells you when the phase is over.

Check the boxes as you make progress, and keep each phase's **Status** line in step with the roadmap table in the [README](../README.md#roadmap): ✅ Done, 🚧 In progress, ⏸ Postponed or ⏳ Not started.

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

**Status:** 🚧 In progress

**Goal:** handle much more traffic without going down, on the same VPS and with the same Docker setup ([ADR 0017](adr/0017-docker-only-infrastructure.md)).

- [x] Load test with k6 to find the bottleneck: [`infra/loadtest/`](../infra/loadtest/) (baseline: 570 requests/s, p95 146 ms in stress mode on one machine, no errors)
- [x] Cache the menu in Redis, optional and fail-safe ([ADR 0019](adr/0019-redis-menu-cache.md)): 570 → 866 requests/s in stress mode; **needs a `redis` container on the server**
- [ ] Pizza photos served through the CDN already in front of the site (Cloudflare), with long cache headers
- [x] Run several copies of the API behind Caddy (Docker replicas), with resource limits per container ([ADR 0020](adr/0020-api-replicas.md)): 708 → 1212 → 1572 requests/s with 1, 2, 4 copies; **the number of copies is set on the server**
- [ ] Database tuning: connection pool size, indexes the load test shows are missing
- [ ] Capacity notes: how far one VPS goes, and what the next step would be (a bigger VPS, a second server)

**Done when:** the system handles 10 times the normal traffic without errors.

**You learn:** scalability, caching, horizontal scaling with containers and load testing. (Kubernetes is out of scope on one VPS: see the ADR.)

---

## Phase 8 (bonus): "I heard hackers attack pizzerias"

**Status:** ⏳ Not started

**Goal:** close the most obvious doors.

- [ ] Passwords and keys kept out of Git (Dokploy environment, GitHub secrets), with a rotation routine written down
- [ ] Scan images for vulnerabilities with Trivy in the pipeline
- [ ] Limit requests per client on the API (rate limiting)
- [ ] Containers running as a non-root user
- [ ] Review the permissions of every token and credential (GitHub, Dokploy, backup storage, Telegram)

**You learn:** the basics of DevSecOps.
