# Phase 3 — The kitchen board

The kitchen needs a screen to see the open orders and move them along. This page
explains how it works and why it is built this way; the full reasoning is in
[ADR 0007](../../../docs/adr/0007-kitchen-login.md) and, for today's login,
[ADR 0024](../../../docs/adr/0024-kitchen-login-in-the-api.md); the settings are in
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
kitchen ──/kitchen/──► Caddy ──► the board's files (public, no data in them)
kitchen ──POST /kitchen/api/session {password}──► Caddy ──► API: password OK? session cookie
kitchen ──/kitchen/api/orders + cookie──► Caddy ──► API: valid session? the orders
anyone else ──/api/orders, PATCH /api/orders/{id}/status──► API: 401
```

How the pieces share the job (since [ADR 0024](../../../docs/adr/0024-kitchen-login-in-the-api.md);
until then Caddy asked for the password in a browser pop-up):

- **The page** asks for the kitchen's password. A login lasts **12 hours** on
  that device, and **Log out** ends it.
- **The API** checks the password against a bcrypt hash (never the password
  itself) and answers with a session cookie the page cannot read. After **5 wrong
  passwords from one address, that address waits 15 minutes**: a script can't
  guess the password, and someone else can't lock the real kitchen out.
- **Caddy** sends the kitchen's calls to the API with the hash and a secret
  token, which only exists on the server. The public `/api` adds neither, so the
  login and the cookie only work on the kitchen's page. Without a hash
  configured, `/kitchen` does not exist (404).

Customers are unaffected: they still read their own order by its id.

## What this does not do yet

It is **one shared login**. Everyone in the kitchen uses the same password, there
are no roles, and nothing records who changed what. That is enough for one
pizzeria and avoids building user management;
[ADR 0024](../../../docs/adr/0024-kitchen-login-in-the-api.md) leaves room for
individual accounts later.
