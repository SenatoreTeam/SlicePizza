# Load test (k6)

`orders.js` simulates customers: every visitor reads the menu (`GET /menu`), one in ten also places an order (`POST /orders`). It uses [k6](https://k6.io) from its Docker image, so nothing is installed.

**Run it only against a local stack, never production**: it creates real orders (named "Load test").

```bash
docker compose up -d --wait db rabbitmq api        # the API on 127.0.0.1:8000
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

**What it says:** the "10 times normal traffic" goal of Phase 7 is reached without changes on this machine, and the limit is far above it (hundreds of requests per second, with the API using about a third of one core). A real pizzeria promo is nowhere near that, so Redis and replicas are a learning exercise, not an emergency. The VPS is slower than a laptop and shares its cores with other projects: **repeat the stress run's numbers as a ratio** (how much faster the menu gets with Redis), not as absolute values.
