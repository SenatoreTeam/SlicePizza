# 0012: The API reports its own metrics, with no new dependency

- **Status:** Superseded by [0016](0016-server-monitoring.md): the API no longer reports metrics, monitoring belongs to the server
- **Date:** 2026-11-17
- **Phase:** 5

## Context

Phase 5 is about knowing something broke before a customer complains. Every container already has a health check (Postgres, RabbitMQ, the API, the worker's heartbeat, the web container through `/api/health`), but those only say *up or down*. To see orders per minute, slow requests, errors, or events piling up in the outbox, the API has to report numbers that Prometheus can collect.

## Options considered

1. **`prometheus_client` (the standard library).** Complete, but a new dependency: the lock files are compiled with hashes for Python 3.15 and every Dependabot update becomes one more thing to review. Its multiprocess mode is only needed with several Uvicorn workers.
2. **Write the text format by hand.** The format is plain text, and the API needs four kinds of numbers. About 100 lines, tested, no new package. The cost: if the API ever runs several workers, the in-memory counters would be per worker, and this would have to move to option 1.
3. **Derive the numbers from the access logs** (Loki, later). Possible, but slower and less exact, and it would make metrics depend on the logging work of the same phase.

## Decision

Option 2, in `api/app/metrics.py`. `GET /metrics` returns:

| Metric | Kind | What it tells |
|---|---|---|
| `slicepizza_http_requests_total{method,route,status}` | counter | traffic and errors per route |
| `slicepizza_http_request_duration_seconds{method,route}` | histogram | latency (buckets from 10 ms to 5 s) |
| `slicepizza_orders_created_total` | counter | orders per minute, with `rate()` |
| `slicepizza_outbox_pending_events` | gauge | events not yet published to RabbitMQ |
| `slicepizza_outbox_oldest_pending_age_seconds` | gauge | how long the oldest one has waited: the "queue piling up" alert |
| `slicepizza_build_info{release,commit}` | gauge | which version runs |

- The `route` label is the route **template** (`/orders/{order_id}`), and requests matching no route share `unmatched`, so a scanner probing random URLs cannot create endless series.
- The scrape itself is not counted.
- **Private by design.** Prometheus reads `api:8000/metrics` on the project network. Caddy answers 404 for `/api/metrics`, like `/api/internal`, and the CI smoke test and the production check both verify it. The numbers contain no customer data: no names, phones, addresses or order ids.
- The outbox gauges are read from the database at each scrape (one small query), so they are right even right after a restart.
- Counters start at 0 when the API restarts; Prometheus' `rate()` handles that.

## Consequences

- No change to the images' dependencies or to the lock files.
- Prometheus, Grafana, dashboards and alerts come in the next steps of Phase 5 and use these names; renaming one later breaks them, so the names are part of the contract.
- The notification worker has no HTTP port and no metrics yet: RabbitMQ's own metrics and the outbox gauges cover "events are not being consumed" for now.
