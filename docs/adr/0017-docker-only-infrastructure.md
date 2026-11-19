# 0017: The infrastructure is Docker on one VPS, with no Terraform, Ansible or Kubernetes

- **Status:** Accepted
- **Date:** 2026-11-19
- **Phase:** 6 and 7

## Context

The first roadmap assumed a cloud account: Terraform to create the network, the virtual machine and the DNS records, Ansible to configure the machine, S3 and IAM for backups, and Kubernetes (k3s) for scale. The real system does not run like that. It runs on a **VPS** (a virtual server bought by the month, with no API to create resources), with Docker and **Dokploy** managing the containers, on a server shared with other projects ([ADR 0016](0016-server-monitoring.md)). DNS is a few records in Cloudflare.

## Options considered

1. **Keep the plan and adopt the tools anyway.** Terraform has nothing to create (the VPS is bought on a website) and Ansible would configure a machine that Dokploy and Docker already manage. It would be exercises with no real system behind them, and more things to keep updated.
2. **Docker only.** Everything the system needs is a container or a file in Git: the backup becomes a container, "rebuild the server" becomes a tested runbook, scaling becomes more containers. What the real server does is what the repository teaches.
3. **Move to a cloud provider to use the tools.** A bigger cost and migration to fit the tools, instead of the tools fitting the system.

## Decision

Option 2.

- **Phase 6** was planned as backups and disaster recovery with containers; it was then taken by the server's owner as a backup of the whole VPS ([ADR 0018](0018-server-backups.md)).
- **Phase 7** scales with what Docker gives on one machine: Redis, several API replicas behind Caddy, resource limits, a CDN already in front (Cloudflare), and k6 load tests. Kubernetes and Helm are removed: on one VPS they add a control plane and no hardware.
- **Phase 8** keeps its goals; "IAM" becomes a review of every token and credential the project uses.
- The rule "no manual changes on the server" stays: what runs is in Git, and what Dokploy keeps outside Git is listed in the runbook.

## Consequences

- No `infra/terraform/`, `infra/ansible/` or `infra/k8s/`; the Terraform lines in `.gitignore` are replaced by ones that keep dumps and keys out of Git.
- The "You learn" of phases 6 and 7 changes from infrastructure as code and Kubernetes to disaster recovery, key custody and container scaling. Terraform, Ansible and Kubernetes can come back if the project ever moves to a cloud.
- One VPS is still one point of failure; the capacity notes of Phase 7 say where the limit is.
