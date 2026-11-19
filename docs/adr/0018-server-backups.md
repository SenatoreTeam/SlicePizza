# 0018: Backups are of the whole VPS, by the server's owner

- **Status:** Accepted
- **Date:** 2026-11-19
- **Phase:** 6

## Context

Phase 6 planned a backup container in this repository: a daily Postgres dump, encrypted, copied offsite, with retention and restore tests ([ADR 0017](0017-docker-only-infrastructure.md)). But SlicePizza is a guest on a shared VPS, and the server's owner already backs up the whole machine, including the Docker volumes where Postgres and RabbitMQ keep their data. This is the same situation as monitoring ([ADR 0016](0016-server-monitoring.md)).

## Options considered

1. **A backup container of our own.** A second copy of what the VPS backup already holds, with its own key, destination and credentials to look after. It would also need a destination that someone pays for and trusts.
2. **The whole-VPS backup only.** One mechanism, one owner, one restore procedure for every project on the server.
3. **Both.** Safer in theory, but twice the work and two things that can be misconfigured.

## Decision

Option 2. Backups and restores belong to the server's owner. This repository implements none; Phase 6 is marked done on that basis. What this repository owes the backup is to stay reproducible: the compose file, the Caddy files and `.env.example` live in Git, and secrets live in the server's `.env`.

## Consequences

- No `infra/backup/` and no `infra/server/` runbook here.
- A restore is as good as the whole-VPS backup: a database dump taken while Postgres is running is consistent only if the VPS backup quiesces it or Postgres can recover from its write-ahead log, which it can after a crash. If a stricter guarantee is ever needed, a `pg_dump` job can be added later without changing this decision's direction.
- The restore has not been exercised from this repository's side; that is for the server's owner to confirm.
