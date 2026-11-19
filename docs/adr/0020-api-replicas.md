# 0020: Several API containers behind Caddy, with resource limits

- **Status:** Accepted
- **Date:** 2026-11-19
- **Phase:** 7

## Context

One API container uses one core at most (one Uvicorn worker, [ADR 0017](0017-docker-only-infrastructure.md) rules out a bigger orchestrator). The VPS has more than one core, and one API that crashes or restarts drops every request meanwhile. The question is how to run more than one copy with what Docker and Dokploy already give.

## Options considered

1. **Several containers of the same service** (`deploy.replicas`), with Caddy sharing the requests. Docker's DNS returns every container's address for the service name.
2. **More Uvicorn workers in one container.** Simple, but one container still dies as a whole, and a limit on memory or processor applies to all workers together.
3. **A separate load balancer container (HAProxy, Traefik).** Caddy is already the way in; another hop adds nothing.
4. **Docker Swarm or Kubernetes.** Out of scope on one VPS ([ADR 0017](0017-docker-only-infrastructure.md)).

## Decision

Option 1.

- `api` has `deploy.replicas: ${API_REPLICAS:-1}`: one copy by default (as before), more by setting the variable. Each copy is limited to **1 processor and 512 MB**. The published port became a range (`127.0.0.1:8000-8009`) so copies do not fight over it; the first is still 8000.
- **Caddy finds every copy by itself**: `reverse_proxy` uses `dynamic a` (asks Docker's DNS every 5 seconds) with `round_robin` and retries another copy for up to 3 seconds. The address is now `API_HOST` / `API_PORT`; the old `API_UPSTREAM=host:port` is still read by the image's start script, so a server that has it keeps working.
- **Safe to copy**: the outbox relay of each API takes a Postgres advisory lock, so order events are published once no matter how many copies run; the rest of the API keeps no state in memory (the menu cache is in Redis, [ADR 0019](0019-redis-menu-cache.md)).

## Consequences

- Measured through Caddy (`SCALE=8 PAUSE=0`, same machine, k6 on it too): **708 requests/s with 1 copy, 1212 with 2, 1572 with 4**, no errors. The gain shrinks because everything, including the load generator, shares the same cores.
- Requests split evenly (14 and 14 of 28 in a check). Stopping a copy under traffic gave one 502 in 60 requests (the request that was already on it); the others were served by the remaining copy.
- Memory limits kill a container that exceeds them: 512 MB is about five times what the API used under load (about 90 MB), so it is a net, not a target.
- **Server step**: in Dokploy, set the number of API copies and make sure `web` has `API_HOST`/`API_PORT` (or `API_UPSTREAM`) pointing at the service name. Dokploy's compose mode honours `deploy.replicas` and limits; if the project is a separate application instead, scale it in its own settings. One copy, as now, works exactly as before.
- **Database connections**: Postgres allows 100 by default and each copy has its own pool. The pool is now explicit and tunable (`DB_POOL_SIZE`, default 5, and `DB_MAX_OVERFLOW`, default 10): at most 15 connections per copy, so 4 copies use at most 60, the worker and RabbitMQ's tools a few more. Go past about 5 copies and the pool or Postgres' `max_connections` must change first.
- **Indexes**: the kitchen's order list filters by status and sorts by date, with no index on either. Left as is on purpose: a pizzeria has thousands of orders, not millions, and the query was not what the load test showed. Adding one to an existing table would also need a migration (`create_all` does not alter tables, [ADR 0002](0002-sqlalchemy-and-schema-creation.md)); revisit when orders reach the hundreds of thousands.
