# 0023: Customers' personal data is replaced after 12 months, by the API itself

- **Status:** Accepted
- **Date:** 2026-11-21
- **Phase:** 9 (LGPD, task 9.3)

## Context

Name, phone and address were kept for ever. LGPD asks for data to be kept only as long as needed for the purpose (Art. 6, III) and deleted when the purpose ends (Art. 15 and 16). The purpose here is to deliver an order and to answer a complaint about it. The data map ([`.lgpd/`](../../.lgpd/data-map.en.md)) also found that `order_events.payload` repeats the customer's name, so deleting only the `orders` columns would not be enough.

## Options considered

1. **Replace the personal fields after a period, keep the order** (this ADR). The numbers (items, totals, dates) are the pizzeria's own and carry no one's identity.
2. **Delete the whole order.** The books would lose history for no privacy gain beyond option 1.
3. **A scheduled job on the server** (Dokploy). Works, but depends on someone setting it up and watching it; if it is forgotten, the policy would be false.
4. **A migration that adds an "anonymized" column.** There are no migrations yet (Phase 10); the job can use the placeholder text itself as the marker.

## Decision

Option 1, run **inside the API** (`api/app/retention.py`) a few times a day, so there is nothing to set up on the server and nothing to forget:

- **Period: 12 months** after the order's last change (`RETENTION_MONTHS`, `0` turns it off), for **finished** orders only (delivered or cancelled). An open order is never touched. The reason for 12 months: long enough for a complaint, a refund dispute or a chargeback, short enough to be a real limit. A lawyer can move it.
- **What changes:** `customer_name`, `customer_phone` and `delivery_address` of the order become `[removed]`; in every event of the order, `customer_name` becomes `[removed]` and the list of Telegram chat ids is emptied; the order's Telegram chat links are deleted. Items, totals, status and dates stay. The order's `updated_at` does not move.
- **Chat links go sooner: 7 days** after the order ends (`RETENTION_CHAT_DAYS`, `0` turns it off): nothing is sent to a finished order, so the chat id has no purpose left.
- **Safe to repeat and to run in several API copies:** a Postgres advisory lock lets one at a time work, and an anonymized order is skipped. It logs counts only, never data.
- **By hand:** `docker compose exec api python -m app.retention --dry-run` counts what would change; without `--dry-run` it does it.

## Consequences

- **Backups keep what they held when taken**, until the server's backup retention expires them (A008 in the data map). A customer's data is therefore gone from the live system at once, and from backups later. The privacy policy (9.2) must say so; the backup retention is a question for the server's owner ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)).
- The orders already stored are not touched until they are 12 months old: the first real effect is in late 2027.
- A complaint about an order older than 12 months can no longer be tied to a name. That is the choice.
- A customer's own request to delete their data sooner (9.4) can reuse the same function for one phone number.
- The placeholder `[removed]` is the marker of "already done". Nothing else in the system writes it.
