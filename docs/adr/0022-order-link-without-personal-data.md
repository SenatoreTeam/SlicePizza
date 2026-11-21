# 0022: The order link carries no personal data

- **Status:** Accepted
- **Date:** 2026-11-21
- **Phase:** 9 (LGPD, task 9.7)

## Context

`GET /orders/<id>` needs no login: the order's random id is the only secret. It used to answer with the customer's **name, phone and delivery address** as well as the progress. A customer forwards the link ("look, my pizza is on the way"), browsers and proxies keep it in histories and logs, and anyone who has it could read where the person lives. The data map ([`.lgpd/`](../../.lgpd/data-map.en.md), A005) flagged it: the page only needs the items and the status.

## Options considered

1. **Remove name, phone and address from the public answer** (this ADR). The order page shows the items, the total and the progress, and says "Delivering to the address you gave us".
2. **Mask the address** (show the street, hide the number). A guess at what is safe, and still personal data.
3. **Require a second secret** (the phone's last digits). More friction for every customer, for data the page does not need.
4. **Leave it and rely on the id being hard to guess.** The id is not the weak point; sharing and logging are.

## Decision

Option 1. `GET /orders/<id>` answers with `OrderPublicOut`: id, status, total, times and items. The details stay in:

- the answer to `POST /orders`, which only the customer who placed the order receives;
- the kitchen's routes (`GET /orders`, `PATCH /orders/<id>/status`), behind the kitchen login;
- the notification events, which still carry only the name (and no phone or address), unchanged.

## Consequences

- A forwarded link now shows only a pizza order and its progress: no one learns who ordered or where.
- The order page no longer shows the address. If a customer wants to check it, they can look at what they typed before ordering; it is a deliberate loss, small next to the exposure.
- **A change to the answer of a public route.** Only this project's own pages call it (the order page; the kitchen uses its own routes), so nothing outside breaks. The version number is a MINOR, not a MAJOR, for that reason.
- The order link can still be found in logs (an IP tied to an order id). That is covered by the log retention work (9.5) and the policy (9.2).
