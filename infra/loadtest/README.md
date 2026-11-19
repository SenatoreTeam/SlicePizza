# Load test (k6)

`orders.js` simulates customers: every visitor reads the menu (`GET /menu`), one in ten also places an order (`POST /orders`). It uses [k6](https://k6.io) from its Docker image, so nothing is installed.

**Run it only against a local stack, never production**: it creates real orders (named "Load test"). Start the API with `ORDER_RATE_LIMIT=0` (the order rate limit, [ADR 0021](../../docs/adr/0021-hardening.md), would otherwise answer 429 to the test).

```bash
ORDER_RATE_LIMIT=0 docker compose up -d --wait db rabbitmq api        # the API on 127.0.0.1:8000
docker run --rm --network host -e SCALE=1 -v "$PWD/infra/loadtest":/t:ro grafana/k6:2.4.0 run /t/orders.js
```

| Variable | Default | Meaning |
|---|---|---|
| `BASE_URL` | `http://127.0.0.1:8000` | Where the API is |
| `SCALE` | `1` | Virtual users = 10 × SCALE. `1` is a normal Friday, `10` is "the R$20 promo" |
| `PAUSE` | `1` | Seconds each user waits between actions. `0` is stress mode: find the limit |

It passes when under 1% of requests fail and 95% answer in under 500 ms.

## Baseline (2026-11-19, one developer machine, API without cache, one worker)

| Run | Users | Requests/s | p95 | Errors |
|---|---|---|---|---|
| `SCALE=1` | 10 | 9 | 15 ms | 0% |
| `SCALE=10` | 100 | 88 | 9 ms | 0% |
| `SCALE=5 PAUSE=0` (stress) | 50, no pause | 570 | 146 ms | 0% |

| `SCALE=5 PAUSE=0`, with the Redis menu cache ([ADR 0019](../../docs/adr/0019-redis-menu-cache.md)) | 50, no pause | 866 | 76 ms | 0% |
| Through Caddy (`BASE_URL=http://127.0.0.1:18080/api`), `SCALE=8 PAUSE=0`, with 1 / 2 / 4 API copies ([ADR 0020](../../docs/adr/0020-api-replicas.md)) | 80, no pause | 708 / 1212 / 1572 | 165 / 130 / 142 ms | 0% |

**What it says:** the "10 times normal traffic" goal of Phase 7 is reached without changes on this machine, and the limit is far above it (hundreds of requests per second, with the API using about a third of one core). A real pizzeria promo is nowhere near that, so Redis and replicas are a learning exercise, not an emergency. The VPS is slower than a laptop and shares its cores with other projects: **repeat the stress run's numbers as a ratio** (how much faster the menu gets with Redis), not as absolute values.

## Capacity notes (Phase 7)

What one VPS can take, from the numbers above (a laptop; the VPS is slower and shared, so treat them as ratios):

- **A normal Friday** is on the order of 10 requests per second at most. One API copy handles about 70 times that in stress mode.
- **"The R$20 promo" (10x)** is covered by one copy with a large margin, so replicas are for **availability** (a copy can restart without dropping requests) more than for speed.
- **The first thing to run out** is the API's processor (one Uvicorn worker per copy, 1 CPU limit): copies scale it almost linearly until the machine's cores are shared with Postgres, Caddy and other projects (1.7x with 2 copies, 2.2x with 4 here).
- **After that**: Postgres' 100 connections (about 5 copies at the default pool), then Postgres itself. Orders (writes) cost more than menu reads, which Redis takes off the database.
- **The next step if one VPS is not enough**: a bigger VPS first (cheapest and needs no change), then a second server with the database moved off it. Both are decisions for the server's owner; nothing in the code blocks them.
- **Not tested**: the VPS itself, the network from outside, and the kitchen and Telegram flows under load. Run this test against the server only with its owner's agreement and without placing real orders.
