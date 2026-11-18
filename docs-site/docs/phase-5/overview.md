# Phase 5 — Overview

**Zé's request:** _"The site went down Friday night and nobody noticed."_

After Phase 4 a change reaches production safely, but nobody was watching what
the system does once it is running. Phase 5 makes the system **say what is
wrong before a customer does**.

:::info Status
This phase is **in progress**. Built and merged: health checks, metrics,
dashboards, logs and Telegram alerts. Not done yet: the down-on-purpose test,
the external uptime check, and putting the monitoring on the server. See the
[roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 5 delivers

- **Health checks** on every service, so Docker and the deploy know what is
  alive.
- **Metrics** ([ADR 0012](../../../docs/adr/0012-api-metrics.md)): the API
  reports orders, latency, errors and the outbox backlog on a private
  `/metrics`.
- **Dashboards** ([ADR 0013](../../../docs/adr/0013-prometheus-and-grafana.md)):
  Prometheus stores the numbers, Grafana shows a SlicePizza overview that lives
  in Git.
- **Logs** ([ADR 0014](../../../docs/adr/0014-loki-and-alloy.md)): Loki keeps 7
  days of every container's logs, Alloy collects them through a read-only Docker
  proxy, and they are searchable in the same Grafana.
- **Alerts** ([ADR 0015](../../../docs/adr/0015-grafana-telegram-alerts.md)):
  Grafana messages a Telegram chat when the API is down, more than 5% of
  requests fail, an order waits more than 5 minutes to reach the kitchen, a
  queue backs up, or the API logs many errors. Each rule must hold for a few
  minutes, so a blip stays quiet. The bot token and chat id are never in the
  repository.

## Good to know

- Prometheus and Loki have no login of their own and **never get a domain**;
  only Grafana is public, behind its login.
- Alerts live inside the same server: if the server is gone, no message. That
  is why an outside uptime check is the next step.
- Logs can contain personal data; they stay on the server and are kept 7 days.
