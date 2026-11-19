# Infrastructure

> 🚧 [`caddy/`](caddy/) is in use. The rest comes in later phases. Monitoring is not here: it belongs to the server ([ADR 0016](../docs/adr/0016-server-monitoring.md)). See the [ROADMAP](../docs/ROADMAP.md).

Everything that describes **where and how** the system runs. The server is a VPS with Docker and Dokploy: there is no cloud provider API, so no Terraform or Ansible ([ADR 0017](../docs/adr/0017-docker-only-infrastructure.md)). Planned structure:

```
infra/
├── caddy/        # The web container: site + /api proxy                 → Phase 2 (ADR 0003)
└── loadtest/     # k6 load test of the API                              → Phase 7
```

Rule from Phase 6 on: **no manual changes on the server.** If it's not here, it doesn't exist. Backups of the VPS are the server owner's ([ADR 0018](../docs/adr/0018-server-backups.md)).
