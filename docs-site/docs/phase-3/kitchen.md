# Phase 3 — The kitchen board

The kitchen needs a screen to see the open orders and move them along. This page
explains how it works and why it is built this way; the full reasoning is in
[ADR 0007](../../../docs/adr/0007-kitchen-login.md), and the settings are in
[DEPLOY.md](../../../docs/DEPLOY.md).

## The board

At **`/kitchen/`** the kitchen sees three columns: **New**, **In the oven** and
**On the way**. Each order is a ticket showing how long it has waited (red after
30 minutes), what to make, and who it is for. One button moves a ticket to the
next step; new orders can also be cancelled, after a confirmation. The board
refreshes every few seconds, tells the kitchen if another screen already changed
an order, and keeps showing the last orders it loaded if the system is
unreachable.

![The kitchen board with orders in three columns](@site/static/img/screenshots/kitchen-board.png)

## Keeping it private

Until this phase, anyone who knew an order's id could change its status, and a
status change now sends a Telegram message to the customer. A list of every order
would also expose phone numbers and addresses. Both are now for the kitchen only.

```
kitchen ──/kitchen/ (user + password)──► Caddy ──► the board's files
kitchen ──/kitchen/api/orders (same login)──► Caddy ──► API
                     Caddy replaces the login with "Authorization: Bearer <token>"
anyone else ──/api/orders, PATCH /api/orders/{id}/status──► API: 401
```

Two layers, each doing the job it is good at:

- **Caddy** asks for a username and password (a bcrypt hash is stored, never the
  password). Without a hash configured, `/kitchen` does not exist (404).
- **The API** accepts the kitchen's requests only with a secret token, which
  Caddy adds after the login. The token lives only on the server, so a browser
  never sees it.

Customers are unaffected: they still read their own order by its id.

## What this does not do yet

It is **one shared login**. Everyone in the kitchen uses the same password, there
are no roles, and nothing records who changed what. That is enough for one
pizzeria and avoids building user management, and
[ADR 0007](../../../docs/adr/0007-kitchen-login.md) says what would change to
support individual accounts. Limiting repeated wrong passwords is left for the
security phase.
