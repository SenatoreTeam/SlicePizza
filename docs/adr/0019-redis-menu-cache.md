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

- **Off unless `REDIS_HOST` is set.** The compose file sets it and runs `redis:8.2.11-alpine`: no disk persistence, 64 MB cap with LRU eviction, read-only filesystem, `cap_drop: ALL`, no published port.
- **Expiry of 60 seconds**, and the key is deleted at API startup after the seed, so a deploy never shows an old menu.
- **Never worse than no cache.** Any Redis error means "use Postgres". The socket timeouts do not cover the DNS lookup of the host name: with the Redis container stopped, one request waited 26 seconds in a test. So every Redis call runs in a helper thread and is abandoned after 0.3 seconds, the cache is then marked down, and a background thread pings Redis every 5 seconds to mark it up again.
- No password: Redis is only on the project's Docker network. If it is ever shared with other projects, set one.

## Consequences

- Measured (same machine, `SCALE=5 PAUSE=0`): from 570 to **866 requests per second** and p95 from 146 ms to 76 ms, 0 errors. The mix has 10% orders, which still hit Postgres.
- Tested: 5 unit tests of the cache, including a Redis that errors and one that hangs; by hand, stopping Redis made one request take 0.3 s and the rest 2 ms, and the cache came back by itself when Redis restarted.
- A price or availability change reaches customers up to 60 seconds late. The API still checks availability and prices from Postgres when an order is created, so no one pays a stale price.
- **Server step**: add a `redis` container to the project in Dokploy and set `REDIS_HOST` on the API (see `docs/DEPLOY.md`). Until then the API runs as before.
- One more image to keep updated (Dependabot watches the compose file).
