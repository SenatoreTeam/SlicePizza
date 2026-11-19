# 0016: Monitoring belongs to the server, not to this repository

- **Status:** Accepted
- **Date:** 2026-11-19
- **Phase:** 5

## Context

ADRs [0013](0013-prometheus-and-grafana.md), [0014](0014-loki-and-alloy.md) and [0015](0015-grafana-telegram-alerts.md) built a monitoring stack inside this repository: Prometheus, Grafana with a SlicePizza dashboard, Loki and Alloy for the logs (through a Docker socket proxy), and Telegram alerts. It ran locally and in CI. It never ran on the server.

SlicePizza does not have the server to itself. It runs as a guest on a server shared by several projects, and that server already has one monitoring stack for the whole machine: Prometheus, Grafana, and exporters for the machine, the containers and the sites. The server's owner keeps it in a repository of their own. It already watches SlicePizza from outside its network:

- each container: running, healthy, restarts, memory and processor;
- the notifications queue and its dead letters, the outbox, the order counts;
- the backups and the version that is live;
- the public sites: `/api/health`, the menu on its three names, and the docs.

A second Prometheus and Grafana for one project would repeat all that. They would bring their own versions to review, like the Prometheus update in #55. They would also put a Docker socket proxy and a second public Grafana domain on a guest.

## Options considered

1. **Keep this repository's stack and run it on the server too.** Two Grafanas watch the same project, with one more set of images and a socket proxy to keep up to date.
2. **Move this repository's dashboard and alerts into the server's stack.** Everything stays in one place, but for now the server's owner keeps only general panels there.
3. **Only the server's monitoring, and remove this repository's stack.** One stack watches the whole machine, and its versions are decided in one place.

## Decision

Option 3, decided by the server's owner on 2026-11-19:

- **Where it lives:** the server's own monitoring repository manages the monitoring and its versions, not this repository.
- **What it shows:** for now, general panels about the server and each project on it. Panels for one service, such as the API's latency by route or orders per minute, are not added for now.
- **What this repository loses:**
  - `infra/monitoring/` (Prometheus, Grafana, Loki, Alloy and their configuration);
  - the `monitoring` profile of `docker-compose.yml`, with the socket proxy;
  - the CI checks of those containers;
  - the images `slicepizza-prometheus`, `-grafana`, `-loki` and `-alloy`, and their Dependabot entries.
- **What the API keeps:** its private `/metrics` ([ADR 0012](0012-api-metrics.md)). It costs nothing, it is tested, and it is ready if a panel for the service comes later. CI now reads it straight from the API's port, and Caddy still answers 404 for `/api/metrics`.

## Consequences

- This ADR supersedes 0013, 0014 and 0015.
- This repository sends no Telegram alerts. Phase 5's "done when" (the alert within 2 minutes) now depends on the server's monitoring.
- The external uptime check (`docs/DEPLOY.md`) is still the project owner's to set up in a hosted service. It runs outside the server, so this decision does not change it.
- The images already published to GHCR stay there until an organization admin deletes them. Nothing pulls them.
- To run the old stack locally (to learn Prometheus or Grafana, for example), use the commit before this ADR: [its `infra/monitoring/`](https://github.com/SenatoreTeam/SlicePizza/tree/42d4bf78dcaba0cb6145556758ec11b9c9373002/infra/monitoring) is in the Git history.
