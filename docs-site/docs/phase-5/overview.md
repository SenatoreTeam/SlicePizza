# Phase 5 — Overview

**Zé's request:** _"The site went down Friday night and nobody noticed."_

After Phase 4 a change reaches production safely, but nobody was watching what
the system does once it is running. Phase 5 makes sure **someone is told when
something breaks**.

:::info Status
This phase is **done** (2026-11-19). The repository first built its own monitoring
(metrics, Prometheus, Grafana, Loki, alerts), then **removed it** in version
1.2.1 ([ADR 0016](../../../docs/adr/0016-server-monitoring.md)): monitoring
belongs to the server SlicePizza runs on, not to this repository. See the
[roadmap](../../../docs/ROADMAP.md).
:::

## What stayed in this repository

- **Health checks** on every service (`/health`, `/api/health`, `/version`, and
  the containers' own checks), so Docker, the deploy and any outside monitor
  know what is alive.

## Why monitoring moved to the server

SlicePizza is a guest on a server shared by several projects. That server
already has one monitoring stack for the whole machine, kept in the server
owner's own repository. It already watches SlicePizza from outside its network:
containers, the notifications queue and dead letters, the outbox, order counts,
backups, the live version and the public sites. A second Prometheus and Grafana
for one project would repeat all of that, add versions to review, and put a
Docker socket proxy and a second public Grafana domain on a guest.

The ADRs [0012](../../../docs/adr/0012-api-metrics.md) to
[0015](../../../docs/adr/0015-grafana-telegram-alerts.md) stay as the record of
what was built and tried (including a down-on-purpose test where the alert
fired 56 seconds after the API stopped), and of why it was removed.
