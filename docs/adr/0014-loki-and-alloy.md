# 0014: Container logs in Loki, collected by Alloy through a read-only Docker proxy

- **Status:** Accepted
- **Date:** 2026-11-17
- **Phase:** 5

## Context

[ADR 0013](0013-prometheus-and-grafana.md) shows numbers. When a number looks wrong, the next question is "what did the API say?", and today that means SSH and `docker logs`. The logs should be searchable in the same Grafana, kept for a few days, on the same server, and without giving a new container the keys to the machine.

## Options considered

1. **Loki + Grafana Alloy + a read-only Docker proxy.** Loki stores, Alloy collects, Grafana (already there) searches. Alloy needs the list of containers and their logs, and the only way Docker offers that is its socket, which is effectively root on the host. A proxy in front of the socket that allows `GET` on containers and networks only removes that power from Alloy.
2. **Loki + Alloy with the Docker socket mounted directly (`:ro`).** Simpler, but `:ro` on a socket restricts nothing: anyone who controls Alloy controls the server. It conflicts with the `cap_drop: ALL` rule on every other container.
3. **Read the JSON files in `/var/lib/docker/containers` instead of the socket.** No socket, but the files are named by container id, so logs would have no service name, and the path is Docker-specific and root-owned.
4. **Promtail.** The older Loki agent, deprecated in favour of Alloy; not a new choice to start with.
5. **Grafana Cloud's logs, or no central logs.** Logs can contain customer names and phone numbers; they stay on the server (same reasoning as ADR 0013).

## Decision

Option 1, in [`infra/monitoring/`](../../infra/monitoring/):

- **Loki** (`grafana/loki`, pinned) as one process on a named volume, **7 days** of retention (the compactor deletes older data), no login of its own. Loki has no "at most N GB" setting, so the limit is age, plus ingestion rate limits per stream so one noisy container cannot fill the disk. Like Prometheus, it must **never get a domain**.
- **Alloy** (`grafana/alloy`, pinned) discovers every container through the proxy, labels each log line with `service` (the compose service) and `container`, and pushes to Loki. It runs as its own non-root user with `cap_drop: ALL`.
- **`tecnativa/docker-socket-proxy`** (pinned, the official project's image, used as published and not rebuilt) is the only container that sees the Docker socket. Only `CONTAINERS` and `NETWORKS` are on (read-only `GET`), `POST` is off: `exec`, `start`, images and volumes answer 403. It runs with a read-only filesystem and `no-new-privileges`.
- **Grafana**: a provisioned `Loki` datasource, and two panels on the overview dashboard: error-looking lines per minute by service, and the recent logs of everything. Searching further is Explore, for example `{service="api"} |= "order"`.
- **Delivery**: same pattern as ADR 0013. `slicepizza-loki` and `slicepizza-alloy` are published as `sha-<commit>` outside the numbered versions; the proxy is used straight from Docker Hub with its tag pinned in the compose. Dependabot watches all three (7-day cooldown).
- Locally and on the server these are in the `monitoring` profile / the monitoring part of the compose.

## Consequences

- Verified locally: Loki answers, Alloy sends logs of every container with its `service` label, Grafana's datasource is healthy and the dashboard has the new panels; through the proxy the container list returns 200 and `images` and `exec` return 403. CI now repeats these checks.
- Alloy collects **every container on the host**, not only SlicePizza's: on a shared server that includes other projects' logs. The 7-day retention covers it; filter by label in `config.alloy` if that becomes a concern.
- Logs can carry personal data (an order's name or phone). The API does not log request bodies today; anything that starts doing so must be treated as personal data (LGPD), and retention is the safety net.
- The disk is protected by age and rate limits, not by size: watch the Loki volume (the dashboard of the server's disk comes with the alerts, 5.5).
- **Not on the server yet**: the three containers in the compose, the two new packages made public, the Loki volume. Steps in `docs/DEPLOY.md`, "Monitoring". The Telegram alerts (5.5) can use Loki too, for example "errors in the last 5 minutes".
