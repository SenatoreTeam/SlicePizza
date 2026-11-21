# Personal data map: SlicePizza

**Version:** v1 | **Status:** Preliminary | **Date:** 2026-11-21
**Technical owner:** Ettore | **Data protection contact (controller):** to be named by the pizzeria (9.2) | **Reviewed by a lawyer:** no
**Method:** reverse engineering of the repository (models, events, worker, web server, front end), as in the skills' legacy pipeline. What is on the server itself is for the server's owner to confirm ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)).

> Not legal advice. Legal bases below are **proposals** for the human check. Articles are of Law 13.709/2018 (LGPD) unless stated.

## 1. Who and what

- **Controller:** the pizzeria that runs the system (in this project, the fictional Zé's Pizzeria; for a real deployment, the real business).
- **Data subjects:** customers who order (adults; **minors are not excluded**: there is no age check, so assume some orders come from teenagers); the kitchen staff (one shared login); whoever is in the pizzeria's Telegram chat.
- **Sensitive data (Art. 5, II):** none collected. No health, allergy, religion or similar fields exist.
- **Large-scale or high-risk (ANPD Res. 2/2022, Art. 4):** preliminarily **no**: small volume, no surveillance, no profiling, no new technology. Revisit if the system grows.
- **Cookies, trackers, analytics:** none. The only browser storage is below (A005). No third-party scripts; one third-party **stylesheet** (A007).

## 2. Processing activities

### A001. Taking an order

| Field | Value |
|---|---|
| Purpose (Art. 6, I) | Receive, prepare and deliver the order the customer asked for |
| Proposed legal basis | Art. 7, V: performance of a contract or preliminary procedures requested by the data subject |
| Data subjects | Customers |
| Data | Name, phone, delivery address, items and total, status and times |
| Origin | Provided by the customer in the order form |
| Where | Postgres: tables `orders`, `order_items` |
| Who sees it | The kitchen (A004); anyone with the order's link (A005); the server's owner (database, backups) |
| Retention today | **Forever**: nothing deletes it |
| Retention proposed | 12 months after the order, then name, phone and address replaced; totals and items stay (task 9.3) |
| Risk | Phone and address identify where a person lives: handle as data to protect, not "just a delivery note" |

### A002. Order events (the outbox) and the queue

| Field | Value |
|---|---|
| Purpose | Tell the kitchen and the customer about a new order and each status change, without losing any ([ADR 0004](../docs/adr/0004-order-events-outbox-rabbitmq.md)) |
| Proposed legal basis | Art. 7, V, as A001 |
| Data | Order id, **customer name**, items, status, and the ids of the Telegram chats following the order. Phone and address are **left out on purpose** |
| Where | Postgres `order_events.payload` (JSON); RabbitMQ queues until the worker reads them |
| Retention today | **Forever** in `order_events` (the outbox keeps published rows as history); the queue drains in seconds |
| Gap | Anonymizing `orders` alone would leave names in `order_events.payload`: **9.3 must cover both** |

### A003. Telegram messages

| Field | Value |
|---|---|
| Purpose | (a) Message the pizzeria's chat about each new order; (b) message a customer about their own order, **only if they chose "Follow on Telegram"** and started the bot |
| Proposed legal basis | (a) Art. 7, V; (b) Art. 7, I: consent, given by the customer's own action. They can stop with the bot's stop command, and the chat is unlinked |
| Data | The customer's Telegram chat id (table `telegram_subscriptions`), the order short id and the customer's name in message texts |
| Third party | **Telegram**: receives and stores the messages and the chat id. Legal role to be confirmed with the lawyer (independent controller for its own service is likely) |
| International transfer | Yes: Telegram's servers are outside Brazil. Mechanism to be confirmed (Art. 33; ANPD Res. 19/2024). The policy must say it |
| Retention | Chat links: forever today (proposal: removed with the order's anonymization). Messages in Telegram: outside our control |
| Notes | The worker logs chat ids (not texts) in some cases; with Telegram off, in development, it logs the message it would send (names) |

### A004. The kitchen board

| Field | Value |
|---|---|
| Purpose | Let the kitchen see and update orders |
| Proposed legal basis | Art. 7, V |
| Data | The orders of A001 in full (name, phone, address); the kitchen's user name |
| Access | One **shared** login (Caddy basic auth, bcrypt hash) and a token between the web and API containers. No attempt limit; not attributable to a person ([`SECRETS.md`](../docs/SECRETS.md)) |
| Browser storage | `localStorage`: the last release notes version the kitchen has seen (no personal data) |

### A005. The customer's own order page

| Field | Value |
|---|---|
| Purpose | Let the customer follow their order |
| Data shown | `GET /orders/<id>` returns **name, phone and address** to **anyone who has the link** (an unguessable random id; no login) |
| Browser storage | `localStorage` key `slicepizza:last-order` holds the order's id on the customer's own device |
| Gap | The link is a bearer secret: anyone it is forwarded to sees the phone and address. A **minimized** status view (items, status, no phone or address) would serve the purpose with less exposure (task 9.7) |

### A006. Access and security logs

| Field | Value |
|---|---|
| Purpose | Operate and defend the service: find errors, spot abuse (the order rate limit, [ADR 0021](../docs/adr/0021-hardening.md)) |
| Proposed legal basis | Art. 7, IX: legitimate interest (a short test is needed); also see Marco Civil da Internet, Art. 15 (access logs of application providers, 6 months), to be checked by the lawyer |
| Data | **IP address**, time, URL (order pages contain the order id, so an IP can be tied to an order), user agent, status. Web container access log; API log; the rate limiter's counters (IP, in memory only, gone at restart); the server's proxy logs |
| Where | Container logs on the server; the server's proxy (Traefik) logs |
| Retention | **Unknown**: depends on the server's Docker and proxy settings ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)) |

### A007. Fonts from Google

| Field | Value |
|---|---|
| What | The menu and kitchen pages load fonts from `fonts.googleapis.com` and `fonts.gstatic.com` |
| Effect | Every visitor's **IP address and browser details go to Google** (outside Brazil) just by opening the page, without being told and without a basis we can defend |
| Fix | Serve the fonts from our own domain (task 9.6, [#82](https://github.com/SenatoreTeam/SlicePizza/issues/82)) |

### A008. Backups and the server

| Field | Value |
|---|---|
| What | The whole VPS is backed up by the server's owner ([ADR 0018](../docs/adr/0018-server-backups.md)), so every table above is in the backups |
| Consequence | A deleted or anonymized customer stays in older backups until they expire: the policy must say so, and the backup retention must be short enough to be reasonable |
| Open | Retention period, encryption, location of the VPS and of the backups ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)) |

## 3. Third parties and their role

| Third party | What it receives | Proposed role | Outside Brazil? | Open |
|---|---|---|---|---|
| Telegram | Chat ids, names in messages | Independent controller (its own service) | Yes | Confirm role and mechanism |
| Google (Fonts) | Visitor IP, browser details | Independent controller | Yes | Remove it (9.6) |
| VPS provider and the server's owner | Everything stored on the server | Processor (Art. 39) | To confirm (VPS location) | #81; a processing agreement between the pizzeria and the server's owner |
| Cloudflare | DNS queries; **all requests if proxied** | Processor | Yes | Is it only DNS, or a proxy? (#81) |
| GitHub | The code, issues, CI logs (no customer data) | n/a | Yes | Keep customer data out of issues and logs |

## 4. Findings, in order of importance

1. **No privacy policy** and no way for a customer to see what we keep: 9.2, 9.4.
2. **No retention**: customer data is kept forever, and `order_events.payload` repeats the name: 9.3.
3. **Google Fonts** sends every visitor's IP to Google: 9.6.
4. **The order link shows phone and address** to whoever holds it: 9.7.
5. **Unknown logs and backups** on the server: #81. A policy cannot promise what we have not confirmed.
6. **International transfer** (Telegram, the VPS): Art. 33 must be addressed in the policy.
7. **Shared kitchen login**: nobody is accountable for a leak; plan in Phase 11 (kitchen login).
8. **Minors** may order: a policy line, and no marketing use of the data.

## 5. Next steps

- Lawyer or encarregado review of the legal bases and the transfer wording.
- Tasks 9.2 to 9.7 in [`docs/ROADMAP.md`](../docs/ROADMAP.md#phase-9-a-customer-asked-what-you-do-with-her-phone-number).
- Re-run this map whenever a new field, a new third party or a new log is added.
