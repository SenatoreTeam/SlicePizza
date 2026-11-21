# Phase 10 — Overview

**Zé's request:** _"We changed the database and it hurt."_

:::info Status
**In progress** (started 2026-11-21). See the [roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 10 delivers

- **Test coverage is measured on every change** (done). The pipeline fails if the tests
  reach less of the code than before: at least 85% of the API and 70% of the worker today.
  The rule: raise the minimum as tests are added, never lower it to let a change pass.

## Planned

- **Database migrations** ([#95](https://github.com/SenatoreTeam/SlicePizza/issues/95)): today
  the API only creates missing tables, so adding a column to an existing table needs manual
  work on the server. Migrations will change the database step by step when a new version
  starts. First the server's real database is checked, so version 1 matches it exactly.
- **A report on every change that touches the database**
  ([#96](https://github.com/SenatoreTeam/SlicePizza/issues/96)): the SQL, and a warning when
  something would delete data.
- **A rule for going back** ([#97](https://github.com/SenatoreTeam/SlicePizza/issues/97)):
  putting the previous version back never undoes a migration, so each migration must also
  work with the previous version.
