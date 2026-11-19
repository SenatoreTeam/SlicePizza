# 0016: Monitoring belongs to the server, not to this repository

- **Status:** Accepted
- **Date:** 2026-11-19
- **Phase:** 5

## Context

ADRs [0012](0012-api-metrics.md), [0013](0013-prometheus-and-grafana.md), [0014](0014-loki-and-alloy.md) and [0015](0015-grafana-telegram-alerts.md) built monitoring inside this repository:

- the API's own metrics, at a private `/metrics`;
- Prometheus, and Grafana with a SlicePizza dashboard;
- Loki and Alloy for the logs, through a Docker socket proxy;
- Telegram alerts.

The stack ran locally and in CI. It never ran on the server, and nothing on the server ever read `/metrics`.

SlicePizza does not have the server to itself. It runs as a guest on a server shared by several projects, and that server already has one monitoring stack for the whole machine: Prometheus, Grafana, and exporters for the machine, the containers and the sites. The server's owner keeps it in a repository of their own. It already watches SlicePizza from outside its network:

- each container: running, healthy, restarts, memory and processor;
- the notifications queue and its dead letters, the outbox, the order counts;
- the backups and the version that is live;
- the public sites: `/api/health`, the menu on its three names, and the docs.

A second Prometheus and Grafana for one project would repeat all that. They would bring their own versions to review, like the Prometheus update in #55. They would also put a Docker socket proxy and a second public Grafana domain on a guest.

## Options considered

1. **Keep this repository's stack and run it on the server too.** Two Grafanas watch the same project, with one more set of images and a socket proxy to keep up to date.
2. **Move this repository's dashboard and alerts into the server's stack.** Everything stays in one place, but for now the server's owner keeps only general panels there.
3. **Only the server's monitoring, and no monitoring code in this repository.** One stack watches the whole machine, and its versions are decided in one place.

## Decision

Option 3, decided by the server's owner on 2026-11-19:

- **Where it lives:** the server's own monitoring repository manages the monitoring and its versions. This repository implements none of it.
- **What it shows:** for now, general panels about the server and each project on it. Panels for one service, such as the API's latency by route or orders per minute, are not added for now.
- **What this repository loses:**
  - the API's `/metrics` (`api/app/metrics.py`, its tests, and the rules for `/api/metrics` in Caddy, CI and the production check);
  - `infra/monitoring/` (Prometheus, Grafana, Loki, Alloy and their configuration);
  - the `monitoring` profile of `docker-compose.yml`, with the socket proxy;
  - the CI checks of those containers;
  - the images `slicepizza-prometheus`, `-grafana`, `-loki` and `-alloy`, and their Dependabot entries.
- **What stays:** the health checks. Docker uses them to know a container is up, and so do the server's version switch and the production check ([ADR 0011](0011-production-check.md)). They are part of running and deploying the system: they do not monitor it.

## Consequences

- This ADR supersedes 0012, 0013, 0014 and 0015.
- Version 1.2.1 takes `/metrics` out of production. Nothing read it, so nothing changes for customers, the kitchen or the server's monitoring.
- This repository sends no Telegram alerts. Phase 5's "done when" (the alert within 2 minutes) now depends on the server's monitoring.
- The external uptime check once proposed for this repository was dropped (2026-11-19, by the project owner): the server's monitoring already watches `/api/health` and the public sites.
- The images already published to GHCR stay there until an organization admin deletes them. Nothing pulls them.
- To run the old stack locally (to learn Prometheus or Grafana, for example), use the commit before this ADR: [its `infra/monitoring/`](https://github.com/SenatoreTeam/SlicePizza/tree/42d4bf78dcaba0cb6145556758ec11b9c9373002/infra/monitoring) and [`api/app/metrics.py`](https://github.com/SenatoreTeam/SlicePizza/blob/42d4bf78dcaba0cb6145556758ec11b9c9373002/api/app/metrics.py) are in the Git history.
