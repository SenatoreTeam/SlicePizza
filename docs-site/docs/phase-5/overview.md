# Phase 5 — Overview

**Zé's request:** _"The site went down Friday night and nobody noticed."_

After Phase 4 a change reaches production safely, but nobody was watching what
the system does once it is running. Phase 5 makes the system **say what is
wrong before a customer does**.

:::info Status
This phase is **in progress**. Built and merged: health checks. The metrics,
dashboards, logs and alerts first built here were removed: monitoring belongs
to the server, which watches every project on it
([ADR 0016](../../../docs/adr/0016-server-monitoring.md)). Not done yet: the
external uptime check. See the [roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 5 delivers

- **Health checks** on every service, so Docker and the deploy know what is
  alive.
- **The server's monitoring**
  ([ADR 0016](../../../docs/adr/0016-server-monitoring.md)): the server
  SlicePizza runs on has one monitoring stack for all its projects. It shows
  SlicePizza's containers (running, healthy, memory, processor), the
  notifications queue, the outbox, the order counts, the backups, the version
  that is live and the public sites. For now its panels are general ones, none
  for one service. This repository implements no monitoring of its own.

## Tried and removed

This repository first had monitoring of its own
([ADR 0012](../../../docs/adr/0012-api-metrics.md),
[0013](../../../docs/adr/0013-prometheus-and-grafana.md),
[0014](../../../docs/adr/0014-loki-and-alloy.md) and
[0015](../../../docs/adr/0015-grafana-telegram-alerts.md)): the API's own
metrics at a private `/metrics`, Prometheus, Grafana with a SlicePizza
dashboard, Loki and Alloy for the logs, and Telegram alerts. It ran locally and
in CI, never on the server, and was removed when the server's monitoring took
that role (version 1.2.1 takes `/metrics` out of the API). The files are in the
Git history.

## Good to know

- Monitoring that runs on the server cannot say the server is gone. That is why
  an outside uptime check, from a hosted service, is the next step
  ([DEPLOY.md](../../../docs/DEPLOY.md#external-uptime-check)).
