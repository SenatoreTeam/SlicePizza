# 0021: Hardening: image scans, secret scans, an order rate limit, no root, a credential review

- **Status:** Accepted
- **Date:** 2026-11-19
- **Phase:** 8

## Context

Phase 8: "I heard hackers attack pizzerias". The system takes real orders, holds customers' names, phones and addresses, and sends messages as the pizzeria's bot. What could be closed cheaply, without new services, on a server the project does not own?

## Decision

1. **Trivy scans every image before it is published** (`build-image.yml`): HIGH and CRITICAL vulnerabilities that have a fix, and secrets left inside. The image is built once locally from the cache, scanned, and only then built again for the push, so a vulnerable image is never published. Accepted findings live in `.trivyignore.yaml` with a reason and an **expiry date**; when it passes, the scan fails again. Trivy is pinned (`aquasec/trivy:0.76.2`) and run as a container, so no third-party GitHub Action has access to the build.
2. **Fixes the first scan asked for**: `pip` is removed from the API and worker images (it carries copies of urllib3, msgpack and setuptools that scans flag, and nothing needs it at run time); `zlib1g` is upgraded when Debian has a fix newer than the base image; Caddy goes from 2.11.8 to 2.11.9. Two findings remain inside the Caddy binary (the Go libraries need a Caddy build that is not published yet) and are in `.trivyignore.yaml`, expiring 2026-12-20.
3. **Gitleaks scans the whole Git history** on every change (`secret-scan` job). The first run found only look-alikes, now listed with a reason in `.gitleaks.toml`.
4. **Order rate limit** (`api/app/ratelimit.py`): 30 orders per 60 seconds per address (`ORDER_RATE_LIMIT`, `ORDER_RATE_WINDOW`; 0 turns it off), then 429 with `Retry-After`. Every order reaches the kitchen and Telegram, so spam costs people's attention. Reading the menu is not limited. No new dependency.
5. **Redis no longer runs as root** (`user: 999:1000`). `api`, `worker` and `web` already did not.
6. **A credential inventory and rotation routine**: [`docs/SECRETS.md`](../SECRETS.md).

## Options not taken

- **A rate limiter in Caddy**: needs a plugin, so a custom Caddy build to maintain; the API-level limit covers the route that matters. The kitchen login stays without one (see `SECRETS.md`).
- **A limit shared between API copies in Redis**: Redis is optional and the server runs one copy; per-copy counters are enough to stop abuse.
- **A secrets manager (Vault and similar)**: another service to run and unseal on one shared VPS, for a handful of secrets. Dokploy's environment and a written rotation routine fit the size.
- **Scanning in a separate nightly workflow only**: would let a vulnerable image be published first.

## Consequences

- A new vulnerability with a fix in a base image can now fail the pipeline on an unrelated PR: that is the point, and the fix is usually a base image or dependency update (Dependabot opens them weekly). If it blocks urgent work, add a dated entry to `.trivyignore.yaml` with a reason.
- **The rate limit trusts the client address from `X-Forwarded-For`.** If the proxies in front were misconfigured so all customers looked like one address, the limit would apply to all of them together: 30 orders a minute for the whole pizzeria. To check after deploying, look at `web`'s access log (`docker logs`) and confirm it shows customers' own addresses, not the proxy's; the live Traefik range must be in `TRUSTED_PROXIES` ([DEPLOY.md](../DEPLOY.md)). A blocked order is logged with the address it was for. If in doubt, set `ORDER_RATE_LIMIT=0` on the API.
- The limit counts per API copy: with N copies the real limit is up to N times higher.
- The load test must run with `ORDER_RATE_LIMIT=0`.
