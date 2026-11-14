# Phase 3 — Events and the queue

The API tells the rest of the system what happens to an order by publishing
**events**. This page explains the idea; the reasoning and alternatives are in
[ADR 0004](../../../docs/adr/0004-order-events-outbox-rabbitmq.md).

## The problem: two places to write

When a customer places an order, the API must save it in PostgreSQL **and** tell
RabbitMQ about it. These are two different systems, so one can succeed while the
other fails:

- Save, then publish: if the publish fails, the order exists but nobody is told.
- Publish, then save: if the save fails, everybody is told about an order that
  does not exist.

## The solution: a transactional outbox

```
POST /orders ─► one database transaction:
                  1. insert the order
                  2. insert an "order.created" row into order_events
                ─► the customer gets their answer

relay thread (in the API) ─► reads unsent rows ─► publishes them ─► marks them sent
```

Because the order and its event are written in **the same transaction**, they
either both exist or neither does. A small relay thread inside the API then
publishes the stored events to RabbitMQ and marks each one as sent. If RabbitMQ is
down, the events stay in the table and go out when it returns.

Details that matter:

- **At least once.** A crash between publishing and marking can publish an event
  twice, so every event carries a unique id and the consumer ignores repeats.
- **No silent loss.** Messages are persistent, the relay waits for RabbitMQ's
  confirmation, and a message that no queue accepts is kept in the table instead
  of being dropped.
- **One publisher.** A PostgreSQL advisory lock makes sure only one API process
  runs the relay at a time.

## What is published

One topic exchange, `slicepizza.events`, with two kinds of event:

| Routing key | When |
|---|---|
| `order.created` | an order is placed |
| `order.status_changed` | its status changes |

Each event is a small JSON document with the order's id, its new and previous
status, and what a notification needs (the customer's name, the pizzas and the
total). The delivery address and phone number are deliberately left out of the
queue. The API works without RabbitMQ configured at all: the events then simply
wait in the table.

The [API reference](../../../api/README.md) lists the settings, and the
[worker README](../../../worker/README.md) shows how to inspect the queues.
