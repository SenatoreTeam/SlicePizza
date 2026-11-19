# Infrastructure

> 🚧 [`caddy/`](caddy/) is in use. The rest comes in later phases. Monitoring is not here: it belongs to the server ([ADR 0016](../docs/adr/0016-server-monitoring.md)). See the [ROADMAP](../docs/ROADMAP.md).

Everything that describes **where and how** the system runs. The server is a VPS with Docker and Dokploy: there is no cloud provider API, so no Terraform or Ansible ([ADR 0017](../docs/adr/0017-docker-only-infrastructure.md)). Planned structure:

```
infra/
├── caddy/        # The web container: site + /api proxy                 → Phase 2 (ADR 0003)
├── backup/       # The backup container: dump, encrypt, upload, prune   → Phase 6
└── server/       # Runbook: rebuild the server from scratch             → Phase 6
```

Rule from Phase 6 on: **no manual changes on the server.** If it's not here, it doesn't exist; what Dokploy keeps outside Git is listed in the runbook.
