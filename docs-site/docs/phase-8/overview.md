# Phase 8 — Overview

**Zé's request:** _"I heard hackers attack pizzerias."_

:::info Status
This phase is **done** (2026-11-19). See the
[roadmap](../../../docs/ROADMAP.md) and
[ADR 0021](../../../docs/adr/0021-hardening.md).
:::

## What Phase 8 delivers

- **Vulnerability scans before publishing.** [Trivy](https://trivy.dev) checks
  every image for serious known vulnerabilities that have a fix, and for
  secrets left inside, **before** the image is published. The first scan found
  something to fix right away: the images carried `pip` and its copies of
  libraries that nothing needed at run time, so `pip` was removed. Two
  findings inside Caddy have no fix yet; they are accepted in a file, with a
  reason and an **expiry date**, so the scan fails again if nobody looks.
- **Secret scan of the whole Git history.** Gitleaks reads every commit on
  every change. The first run found only look-alikes (a test's made-up token
  and a default demo password), now listed with the reason.
- **A limit on orders.** One address can place 30 orders a minute; after that
  the API answers "too many" and says when to retry. Every order reaches the
  kitchen and Telegram, so spam costs people's attention, not only computer
  time. Reading the menu is never limited.
- **No root.** `api`, `worker`, `web` and `redis` run as ordinary users.
  Postgres and RabbitMQ start as root only to fix their folders, then change
  user, which is how their official images work.
- **A list of every secret.** [`docs/SECRETS.md`](../../../docs/SECRETS.md): what
  each one protects, where it lives, how powerful it is, and how to replace it.

## Good to know

- The order limit trusts the customer's address sent by the proxies in front.
  If they were misconfigured so everyone looked like one address, the limit
  would apply to everybody together, so the deploy guide says how to check.
- Not everything is in this repository: the server's own passwords, SSH keys
  and backups belong to its owner, so the review lists them as "to confirm".
- Security is a routine, not a feature: the expiry dates, the weekly
  dependency updates and the yearly secret rotation are what keep it true.
