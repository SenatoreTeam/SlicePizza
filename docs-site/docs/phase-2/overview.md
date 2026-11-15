# Phase 2 — Overview

**Zé's request:** _"I want the site live on my own domain."_

Phase 1 ended with everything running on one laptop. In Phase 2 the system gets a
public address, **https://slicepizza.senatore.tech**, and a menu website that
customers can use from their phones.

:::info Status
This phase is **done**. The system has been live at
https://slicepizza.senatore.tech since 2026-11-15, and an order has been placed
through the live site. See the [roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 2 delivers

- A **menu website** in plain HTML, CSS and JavaScript (no build step): the
  customer picks pizzas, places an order and follows it on a status page.
- A **Caddy** container in front of the API that serves the site at `/` and the
  API at `/api`, so everything lives on one domain.
- Images published automatically to GitHub's container registry on every merge,
  and picked up by the server within about five minutes.
- Lock files with hashes for the API's dependencies, so the same packages are
  installed every time.

## The problem this phase creates

The system is public now, but it is a single moving part: orders are only
**recorded**. Nobody is told when one arrives, and the customer has to keep
reloading the status page to learn that the pizza is on its way. In Phase 3, Zé
asks for customers to be told.

Continue with [the site and the proxy](./site-and-proxy.md).
