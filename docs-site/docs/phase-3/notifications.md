# Phase 3 — Telegram notifications

A separate service, the **worker**, reads events from RabbitMQ and sends the
Telegram messages. This page explains how it behaves; the setup steps are in the
[worker README](../../../worker/README.md), and the decisions are in
[ADR 0005](../../../docs/adr/0005-notification-worker.md) and
[ADR 0006](../../../docs/adr/0006-customer-telegram-opt-in.md).

## Who gets what

- **The pizzeria's chat** gets a message when an order arrives and when its
  status changes.
- **Customers** get messages only if they asked. On the order page, **Follow on
  Telegram** opens the bot with the order's id, and pressing _Start_ links that
  chat to the order. `/stop` unlinks it. Nobody is messaged without doing this.

The button is shown only when the site knows the bot's username
(`TELEGRAM_BOT_USERNAME`), and only while the order is still on its way.

## The queue protects the messages

The worker reads from a durable **quorum queue** called `notifications`. A
message is removed only **after** Telegram has accepted it, and the worker takes
one message at a time. So:

- **Worker down:** messages wait in the queue and are sent when it returns. This
  is the goal of the phase, and a CI test proves it by stopping the worker,
  placing an order, starting the worker and checking the message arrives.
- **Telegram slow or failing:** the worker waits and tries again, honouring
  Telegram's "retry after" requests.
- **Wrong setup** (a bad bot token, say): the worker keeps the message and keeps
  trying instead of throwing it away, so fixing the setting is enough.
- **A message that can never be delivered** (rejected by Telegram) goes to a
  **dead-letter queue** where it can be inspected, instead of blocking the line.
- **A customer who blocked the bot** is skipped and unlinked.

Each message is sent at most once per event and chat, even if RabbitMQ delivers
the event twice.

## Who owns the data

The API, not the worker, stores which chats follow which order (a
`telegram_subscriptions` table). The worker asks the API over a small internal
route protected by a shared secret, `INTERNAL_API_TOKEN`; Caddy never forwards
these routes to the internet. Each event then carries the list of chats to
notify, so the worker needs no database of its own.

Without a bot token the worker still runs and only **logs** what it would send,
which is how local development and the automatic checks work. Customers' names
appear in those logs, so that mode is not for production.
