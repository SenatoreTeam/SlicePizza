# Phase 12 — Overview

**Zé's request:** _"It broke at 7 p.m. on Friday."_

:::info Status
**In progress** (started 2026-11-21). See the [roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 12 delivers

- **The health check tells about stuck orders** (live since version 1.6.0).
  `/api/health` now says `"outbox":"late"` when an order update has waited more than
  5 minutes to leave for Telegram, so a monitor can warn before customers notice. It still
  answers "healthy", on purpose: a Telegram or RabbitMQ problem must not make the server
  roll back or restart the API, which would not fix it.

## Planned

- **Break a version on purpose** and time how the server puts the old one back, and **restore
  a backup with our data**, with the server's owner
  ([#103](https://github.com/SenatoreTeam/SlicePizza/issues/103)).
- **Runbooks** for a bad evening: the kitchen cannot see orders, Telegram is silent, the site
  is slow ([#100](https://github.com/SenatoreTeam/SlicePizza/issues/100)).
- **Docs for people**: a quick start, a glossary, a FAQ, and a short manual for the kitchen
  in Portuguese ([#102](https://github.com/SenatoreTeam/SlicePizza/issues/102)).
