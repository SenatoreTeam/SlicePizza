# 0013: Prometheus and Grafana, on the same server, from files in Git

- **Status:** Superseded by [0016](0016-server-monitoring.md): the server's own monitoring replaces this stack
- **Date:** 2026-11-17
- **Phase:** 5

## Context

[ADR 0012](0012-api-metrics.md) made the API report numbers. Something has to collect them over time and show them. The monitoring runs **on the same server** as the system (decided for Phase 5), so it has to be light, and it has to reach the API and RabbitMQ on their private project network: those ports are not public.

## Options considered

1. **Prometheus + Grafana, self-hosted** next to the system. Free, teaches the real stack, and reads the private network directly. If the whole server dies, the monitoring dies with it (a separate outside check covers that case, later in this phase).
2. **Grafana Cloud's free tier.** Nothing to run, survives a server outage, but metrics would leave the server, and an agent still has to run next to the system.
3. **Only the containers' health checks and logs.** Says up or down, never "slower than yesterday" or "orders stopped".

## Decision

Option 1, in [`infra/monitoring/`](https://github.com/SenatoreTeam/SlicePizza/tree/42d4bf78dcaba0cb6145556758ec11b9c9373002/infra/monitoring) (removed by ADR 0016; the link shows the last version):

- **Prometheus** (`prom/prometheus`, pinned) scrapes every 15 s: the API (`api:8000/metrics`), RabbitMQ's built-in exporter (`rabbitmq:15692`, on by default in the official image) and itself. It keeps **15 days and at most 2 GB**: a full disk would take the whole server down.
- **Grafana** (`grafana/grafana`, pinned) with the datasource and the **SlicePizza overview** dashboard **provisioned from files**: services up, orders per minute, the release running, requests by status, 5xx per minute, latency p95 by route, the outbox backlog and its oldest event, and RabbitMQ's messages. Dashboards are read-only in the browser: to change one, change the file in Git, like the rest of the project. Sign-up and anonymous access are off, and Grafana's reporting to its vendor is off.
- Both run with `cap_drop: ALL` and `no-new-privileges`, like the other containers. Neither publishes a port to the internet. Grafana alone gets a domain, behind its login; Prometheus has no domain and no login of its own, so it must never get one.
- **Delivery: two small images, like `web`.** `infra/monitoring/prometheus/Dockerfile` and `infra/monitoring/grafana/Dockerfile` put the configuration inside the official images, and the pipeline publishes `ghcr.io/senatoreteam/slicepizza-prometheus` and `-grafana` as `sha-<commit>` after the same checks. The server's compose then needs no copy of this repository's files. They are **not part of the numbered versions**: they change rarely, so the server pins the `sha-` tag it runs and moves it by hand when the configuration changes, and the version flow (ADR 0009) and its "all three images or none" rule stay as they are. Dependabot watches their base images.
- Locally: `docker compose --profile monitoring up -d`. The profile keeps CI and everyday development unchanged: nothing starts without it.
- Versions follow the project's 7-day rule: both were public for a week or more when chosen.

## Consequences

- Verified locally with the real stack: all three targets `up`, the order created by a test shows in `slicepizza_orders_created_total`, Grafana finds the datasource and the dashboard.
- RabbitMQ's default exporter sums all queues (per-queue numbers need a second endpoint), so the dashboard shows the total of ready and unacknowledged messages. Per-queue detail can come with the alert on the dead-letter queue.
- CI checks the real thing on every run: it starts the two images next to the stack and requires the three targets (`api`, `rabbitmq`, `prometheus`) to be up, Grafana's datasource to answer, and the dashboard to be found.
- **Not on the server yet.** What is left is on the server itself: adding the two containers to the compose, a DNS record and a Dokploy domain for Grafana, and its admin password (docs/DEPLOY.md, "Monitoring"). The Telegram alerts (Alertmanager or Grafana alerting) build on the same two containers.
