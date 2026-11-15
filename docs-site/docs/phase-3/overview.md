# Phase 3 — Overview

**Zé's request:** _"Customers want to know when their pizza is on the way."_

In Phase 3 every status change becomes a message: to the pizzeria's Telegram
chat when an order arrives, and to customers who ask for it as their order moves
along. The kitchen also gets a screen to run the orders from.

:::info Status
This phase is **done**. The kitchen board, the queue, the worker and the
Telegram messages have been live at https://slicepizza.senatore.tech since
2026-11-15, and an order placed on a phone was followed on Telegram from start
to finish. See the [roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 3 delivers

- **RabbitMQ** as a message queue, and an **outbox** in the API so an order and
  its event are always saved together. See [Events and the queue](./events.md).
- A **notification worker** that reads the queue and sends Telegram messages, to
  the pizzeria's chat and to customers who tap **Follow on Telegram**. See
  [Telegram notifications](./notifications.md).
- A **kitchen board** at `/kitchen`, behind a login, where the kitchen moves
  orders along. See [The kitchen board](./kitchen.md).

## Why a queue at all

The API could call Telegram itself when a status changes. Then a slow or broken
Telegram would slow down or fail the customer's order, and a restart at the wrong
moment would lose a message. With a queue the API only records what happened and
returns immediately. A separate worker does the slow part, at its own pace, and
messages wait safely while it is down.

## The problem this phase creates

There are now four services (API, site, queue, worker) and several secrets, all
updated by merging to `main` and waiting for the server. Every change is checked
by hand, and nothing says whether the live system is healthy. Phases 4 and 5
(automation and observability) answer that.
