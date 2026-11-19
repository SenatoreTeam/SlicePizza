# Phase 6 — Overview

**Zé's request:** _"The server died and we lost the orders."_

:::info Status
This phase is **done** (2026-11-19), by the server's owner. See the
[roadmap](../../../docs/ROADMAP.md).
:::

## What happened to this phase

The plan was Terraform and Ansible to rebuild a cloud server, and S3 for
backups. The real system is a **VPS with Docker and Dokploy**, so:

- **No Terraform and no Ansible**: there is no cloud API to create resources
  from, and Docker and Dokploy already manage the machine
  ([ADR 0017](../../../docs/adr/0017-docker-only-infrastructure.md)).
- **Backups belong to the server's owner**: the whole VPS is backed up,
  including the Postgres and RabbitMQ data, the same way monitoring is the
  server's job ([ADR 0018](../../../docs/adr/0018-server-backups.md)).

What this repository owes is to stay **reproducible**: the compose file, the
Caddy files and `.env.example` live in Git, and secrets live only in the
server's `.env`.
