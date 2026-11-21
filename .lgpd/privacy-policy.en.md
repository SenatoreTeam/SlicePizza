# Privacy Policy (DRAFT)

> **DRAFT. DO NOT PUBLISH** before: (1) review by a lawyer or the data protection officer; (2) Miguel's answers to the questions in [#81](https://github.com/SenatoreTeam/SlicePizza/issues/81) (logs, backups, Cloudflare, server location); (3) the pizzeria's real name and contact. Parts in **[brackets]** are open. Based on the data map v1 ([`data-map.en.md`](data-map.en.md)). Not legal advice. The Portuguese text is the main one ([`privacy-policy.md`](privacy-policy.md)).

**Version:** draft 1 · **Date:** 2026-11-21

This policy explains, in plain words, how **[PIZZERIA NAME]** handles the personal data of people who order through our website.

## 1. Who is responsible for your data

**[PIZZERIA NAME]**, **[tax id]**, **[address]**, is the controller: it decides how and why your data is used.
**Privacy contact:** **[name or "Data protection officer"]**, **[e-mail]**, **[phone/WhatsApp]**.

## 2. What data we collect and why

| Data | Why | Legal basis (LGPD, Art. 7) |
|---|---|---|
| **Name, phone and delivery address** (typed into the order) | Receive, prepare and deliver your order; reach you if there is a delivery problem | V: performance of a contract (the order) |
| **Items and total of the order, date and status** | The same, and the pizzeria's accounts | V: performance of a contract |
| **Your Telegram chat code** (only if you tap "Follow on Telegram" and start the bot) | Tell you about each step of the order | I: your consent. You can stop at any time by sending `/stop` to the bot |
| **IP address, time and page visited** (server logs) | Keep the site running and protect it from abuse | IX: the pizzeria's legitimate interest in security **[confirm the legitimate-interest test]** |

We collect no sensitive data (health, religion and the like). We use no tracking cookies, no analytics and no advertising. The site keeps only the code of your last order in your browser, so you can find it again.
**[Children and teenagers: the site is not aimed at people under 18. If a minor places an order, we use the data only to deliver it and never for marketing.]**

## 3. Who we share it with

- **Our kitchen**: sees name, phone and address to prepare and deliver.
- **Telegram**: receives the messages we send (the customer's name and the order code) and keeps the chat code of those who chose to follow. Telegram is a separate service with its own policy, and is **outside Brazil** **[confirm the transfer mechanism]**.
- **The server provider and whoever runs it**: store the system's data. **[Provider name; server location: confirm (#81). If outside Brazil, say so here.]**
- **[Cloudflare]**, only if **[confirm: DNS only, or it carries the traffic]**.
- We do not sell your data and do not use it for third parties' advertising.

## 4. How long we keep it

- **Name, phone and address of an order: 12 months** after the order ends (delivered or cancelled). Then they are **replaced** by `[removed]`; only the items and totals stay, identifying no one.
- **Your Telegram chat code: 7 days** after the order ends.
- **Server logs (IP, time, page): [period; confirm with the server's owner, #81]**.
- **Server backups** may hold older data for **[period; confirm, #81]**, and are then deleted.

## 5. Your rights

At any time and at no cost you can ask us to: **confirm** whether we process your data; give you **access** to it; **correct** it; **erase** (anonymize) data that is unnecessary or based on consent; tell you **who we share it with**; **withdraw consent** (Telegram: `/stop`); and you can **complain to the ANPD** (Brazil's data protection authority).
Ask through the contact in section 1, on any channel. We answer simple requests at once and a complete answer **within 15 days**. For your safety, we **check it is you** by calling or writing to the phone number on the order (we never ask for a document).

## 6. Security

We use a protected connection (HTTPS), a password for the kitchen, an order limit per address against abuse, security scans before publishing new versions, and automatic deletion of old data. No system is perfect: if an incident could harm you, we will tell you and the ANPD as the law requires.

## 7. Changes to this policy

When we change this policy, we will publish the new version here, with its date. The site's code and change history are public: <https://github.com/SenatoreTeam/SlicePizza>.

---

## For the review (do not publish this part)

- [ ] Name, tax id, address and the data protection officer's contact filled in (Art. 41: appointing the officer, unless the ANPD exempts small businesses).
- [ ] Legal bases checked by a lawyer (mainly IX for the access logs, and I for Telegram).
- [ ] International transfer (Art. 33): Telegram and, if applicable, the server: mechanism confirmed and stated above.
- [ ] Log and backup periods filled in from Miguel's answer (#81).
- [ ] The 12-month period approved (ADR 0023).
- [ ] Text about minors (ECA Digital) reviewed.
- [ ] The page is linked from the order form and the footer, and the English version matches.
- [ ] The retention values in the code (`RETENTION_MONTHS`, `RETENTION_CHAT_DAYS`) match section 4.
