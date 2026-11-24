# 0019: An optional Redis cache for the menu, that can never make the API worse

- **Status:** Accepted
- **Date:** 2026-11-19
- **Phase:** 7

## Context

Every visitor reads the menu, and the menu almost never changes: it is written once at startup (the seed) and has no edit route. Each read was a Postgres query. The load test ([`infra/loadtest/`](../../infra/loadtest/)) shows the API already handles far more than a real promo, so this is a learning step with a measurable gain, not an emergency.

## Options considered

1. **Redis, optional, with a short expiry.** A cache shared by every API copy, which matters once there are replicas.
2. **A cache inside each API process.** No new container, but each replica has its own copy and nothing to teach about shared caches.
3. **HTTP caching in Caddy or the CDN only.** Cheap, and still planned for the pizza photos, but the menu is an API answer that the browser shows fresh; Caddy would need a cache plugin.
4. **No cache.** Honest at this size, but Phase 7 asks for it.

## Decision

Option 1, in `api/app/cache.py`:

- **Off unless `REDIS_HOST` is set.** The compose file sets it and runs `redis:8.10.3-alpine` (8.2.11 until #108): no disk persistence, 64 MB cap with LRU eviction, read-only filesystem, `cap_drop: ALL`, no published port.
- **Expiry of 60 seconds**, and the old copy is deleted before the cache is used, so a deploy never shows an old menu. The watcher does it (see below) when it first reaches Redis, and again after every error. Until 1.6.2 the API tried to delete it right after the seed, before the cache was up, so nothing was deleted and a restart could show the old menu for up to 60 seconds.
- **Never worse than no cache.** Any Redis error means "use Postgres". The socket timeouts do not cover the DNS lookup of the host name: with the Redis container stopped, one request waited 26 seconds in a test. So every Redis call runs in a helper thread and is abandoned after 0.3 seconds, the cache is then marked down, and a background thread (the watcher) pings Redis every 5 seconds to mark it up again.
  Since 1.6.2:
  - A call given up on before it started is cancelled, so it never writes to Redis late.
  - The helper threads are daemons, so a call stuck in a DNS lookup does not hold up the API's shutdown.
  - An entry that is not a valid menu counts as an error, and the watcher then deletes it. That covers an entry that is not JSON, is not a list, or does not match the menu's shape (`list[PizzaOut]`, checked in `main.py`). During a deploy with several API copies ([ADR 0020](0020-api-replicas.md)), an older copy may still write the menu in its own shape.
  - A `REDIS_PORT` that is not a number turns the cache off with a warning, instead of stopping the API.
  - The watcher logs once when Redis cannot be reached, also when it was never reached (wrong host or password).
- **The client's settings are written in `cache.py`, not left to redis-py's defaults**, which changed in redis-py 8 (#111): RESP3 and 10 retries with backoff. The cache uses **RESP2** (`protocol=2`), which works with any Redis and is all the cache needs. It allows **one immediate retry** (`Retry(NoBackoff(), 1)`), which replaces a connection closed by a Redis restart; the watcher does the slow retrying.
- No password: Redis is only on the project's Docker network. If it is ever shared with other projects, set one.

## Consequences

- Measured (same machine, `SCALE=5 PAUSE=0`): from 570 to **866 requests per second** and p95 from 146 ms to 76 ms, 0 errors. The mix has 10% orders, which still hit Postgres.
- Tested: 5 unit tests of the cache, including a Redis that errors and one that hangs; by hand, stopping Redis made one request take 0.3 s and the rest 2 ms, and the cache came back by itself when Redis restarted.
- Since 1.6.2 there are unit tests for each case above: a damaged entry, the old copy dropped before use, a Redis never reached, a call given up on, the daemon threads, a bad `REDIS_PORT`, and the client's settings. Since #108 the CI smoke test also checks that the menu really goes into Redis: `/menu` answers either way, so before that check a broken cache still passed CI.
- A price or availability change reaches customers up to 60 seconds late. The API still checks availability and prices from Postgres when an order is created, so no one pays a stale price.
- **Server step**: add a `redis` container to the project in Dokploy and set `REDIS_HOST` on the API (see `docs/DEPLOY.md`). Until then the API runs as before.
- One more image to keep updated (Dependabot watches the compose file).
