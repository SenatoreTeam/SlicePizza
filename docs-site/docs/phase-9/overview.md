# Phase 9 — Overview

**Zé's request:** _"A customer asked what you do with her phone number."_

:::info Status
**In progress** (started 2026-11-21). Most of it is live since version 1.5.0; the
privacy policy waits for a legal check and for answers from the server's owner. See the
[roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 9 delivers

- **A map of the personal data we keep** (in [`.lgpd/`](../../../.lgpd/data-map.en.md)):
  name, phone and address of each order, and the Telegram chat of customers who follow one.
  It found two problems, fixed below.
- **No more Google Fonts.** The pages sent every visitor's address to Google to load the
  fonts; now the fonts come from our own domain.
- **The order link shows no personal data.** Whoever has the link sees the pizzas and the
  status, not who ordered or where ([ADR 0022](../../../docs/adr/0022-order-link-without-personal-data.md)).
- **Old data is removed by itself.** 12 months after an order ends, its name, phone and
  address are replaced; Telegram chat links go after 7 days
  ([ADR 0023](../../../docs/adr/0023-retention-of-personal-data.md)).
- **A customer can ask what we keep, or to be erased.** One command answers it, with a
  [step-by-step guide](../../../docs/PRIVACY-REQUESTS.md).

## Still to do

- **The privacy policy** is drafted in English and Portuguese, but it is not on the site:
  it needs a legal check, the pizzeria's real details, and answers about the server's logs
  and backups ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)).
