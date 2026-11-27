# Phase 11 — Overview

**Zé's request:** _"How do I know nobody tampered with what we run?"_

:::info Status
**In progress** (started 2026-11-21). See the [roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 11 delivers

- **Everything we run is pinned.** Each step of the pipeline points to an exact commit, and
  each base image to an exact digest, so a tag moved by someone else cannot change what we
  build. Dependabot proposes the updates, grouped.
- **A place to report a vulnerability** privately ([`SECURITY.md`](../../../SECURITY.md)), a
  code of conduct, and issue templates. GitHub's secret scanning blocks a push with a secret.
- **Search engines stay out** of the API and the kitchen board.
- **Who reviews what** ([`CODEOWNERS`](../../../.github/CODEOWNERS)): a change to the pipeline,
  the images, the server files or the versions asks both of us to review; a change to the
  login, the rate limit or the database asks Ettore.
- **A safer kitchen login** ([ADR 0024](../../../docs/adr/0024-kitchen-login-in-the-api.md)): a
  login page instead of the browser's pop-up, 15 minutes locked after 5 wrong passwords from
  one address, and a session that ends after 12 hours, with a Log out button. It needed no
  change on the server. Testing it against a copy of the server in Docker showed every
  customer looked like one address; Caddy now passes each customer's real address, which
  also fixes the order limit.

## Planned
- **Confirm the server's own security** and **rotate every secret once**, to prove the
  routine in [`SECRETS.md`](../../../docs/SECRETS.md) works
  ([#99](https://github.com/SenatoreTeam/SlicePizza/issues/99),
  [#103](https://github.com/SenatoreTeam/SlicePizza/issues/103)).
