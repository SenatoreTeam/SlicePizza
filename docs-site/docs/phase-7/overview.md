# Phase 7 — Overview

**Zé's request:** _"We're running a R$20 pizza promo on Friday."_

:::info Status
This phase is **done** (2026-11-19). Two parts need the server's owner: a
`redis` container and the number of API copies. See the
[roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 7 delivers

- **A load test** with [k6](https://k6.io) in `infra/loadtest/`: customers
  reading the menu, one in ten ordering. The first result was a surprise: **10
  times a normal Friday already passed**, with 570 requests per second in
  stress mode. A real promo is far below that.
- **A Redis menu cache**
  ([ADR 0019](../../../docs/adr/0019-redis-menu-cache.md)): off unless
  configured, and built so that Redis being down or slow never makes the API
  worse (a test showed that a stopped Redis made one request wait 26 seconds
  before it was fixed). 570 → 866 requests per second.
- **Several API containers behind Caddy**
  ([ADR 0020](../../../docs/adr/0020-api-replicas.md)): Caddy finds every copy
  through Docker's DNS and shares the requests. 708 → 1212 → 1572 requests per
  second with 1, 2 and 4 copies. The outbox relay was already safe to run more
  than once (a database lock).
- **Capacity notes**: what one VPS can take and what to do when it is not
  enough.

## Not Kubernetes

On one VPS, Kubernetes adds a control plane and no hardware. The scale here
comes from what Docker already gives
([ADR 0017](../../../docs/adr/0017-docker-only-infrastructure.md)).

## What the numbers teach

Replicas matter more for **availability** (a copy can restart without dropping
requests) than for speed, at this size. And measure before and after: the cache
gained 50% only because the test showed where the time went.
