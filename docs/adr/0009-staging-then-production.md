# 0009: The pipeline deploys: staging first, then production, by moving image tags

- **Status:** Accepted
- **Date:** 2026-11-15
- **Phase:** 4

## Context

After [ADR 0008](0008-one-gated-pipeline.md), only tested commits become images. But the deploy itself was still blind:

- On `main`, the pipeline published `:latest`, and Dokploy's auto-update on the server picked it up **within 5 minutes**. Nothing told GitHub whether the new version started, and a version that passed the tests but failed on the server (a missing setting, a schema the database doesn't have) was only noticed by a customer.
- There was **one environment**. The first place a change met real HTTPS, the real proxy and a deployed database was production.
- The roadmap asks for a staging environment at `staging.<domain>`, an automatic deploy after a merge, and the deploy's secrets in GitHub.

Constraints:

- The server is **shared** and administered in Dokploy. The project has no API key for Dokploy (it can do anything on the server), only what each service offers: Dokploy gives every compose service a **deploy webhook** that redeploys that one service.
- The containers have hard limits (512 MB, 1 CPU each), and the server runs other projects: a second environment must be small.
- One Telegram bot can have only one reader ([ADR 0006](0006-customer-telegram-opt-in.md)), so staging can't share production's bot.

## Options considered

How the pipeline deploys:

1. **Keep the 5-minute polling, and only wait and check** from the pipeline. No new secrets, but a deploy takes up to 5 minutes to start, and staging would need polling too.
2. **SSH from GitHub Actions** and run `docker compose pull && up -d`. Fast and explicit, but an SSH key to a shared server in GitHub, with far more power than a deploy needs.
3. **Dokploy's API** (`compose.deploy`): exact, but needs an API key with power over the whole server.
4. **Dokploy's deploy webhook**, one per environment: it can only redeploy its own service, so leaking it costs a redeploy and nothing more.

Which version each environment runs:

- **Rebuild the images for production** after staging: production would not run the exact images that were tested.
- **Each environment's compose names a commit** (`slicepizza-api:sha-...`): exact, but the pipeline would have to edit the service's settings in Dokploy, which the webhook can't.
- **A moving tag per environment**: `staging` and `latest` (production). The pipeline moves the tag to the tested `sha-<commit>` images (a registry operation, nothing is rebuilt or downloaded), then asks Dokploy to deploy.

## Decision

Option 4, with a moving tag per environment.

```
merge into main ──► pipeline: lint ─► tests ─► images (sha-<commit>)
                                                  │
              :staging ──► sha-<commit> ◄─────────┤
              staging webhook ──► Dokploy deploys staging
              check_deploy.py: staging runs <commit>? place an order, kitchen moves it
                                                  │ only if all passed
              :latest ───► sha-<commit> ◄─────────┘
              production webhook ──► Dokploy deploys production
              check_deploy.py: production runs <commit>? read-only checks
```

- **Staging** is a second Dokploy compose on the same server, at `https://staging.slicepizza.senatore.tech`, from [`infra/dokploy/docker-compose.yml`](../../infra/dokploy/docker-compose.yml) with `SLICEPIZZA_TAG=staging`. It has its own database, RabbitMQ, secrets and kitchen password, and no Telegram bot by default (the worker logs the messages; staging only has test orders).
- **Production** keeps its compose; its images stay on `:latest`, which now moves only after staging passed.
- **`deploy.sh`** checks that the three `sha-<commit>` images exist, moves the environment's tag on all three, then calls the environment's webhook and requires HTTP 200 (Dokploy answers 301 or 400 when it decides not to deploy).
- **`check_deploy.py`** waits up to 10 minutes until `/version` (web) and `/api/health` (API) both report the commit ([ADR 0008](0008-one-gated-pipeline.md)), then checks the site, the menu, the docs, and that the private routes stay private. On staging it also places an order and, with the kitchen's password, moves it along on the board. Production is never written to.
- **Secrets live in GitHub environments** (`staging`, `production`): `DEPLOY_WEBHOOK_URL` in each, and the staging kitchen's `KITCHEN_PASSWORD`. Without a webhook the pipeline falls back on Dokploy's auto-update and still checks the version.
- **A red stage stops the line**: a failed staging deploy or check means production is not touched.
- **Rollback** is a manual workflow, "Roll back production": it moves `latest` back to an earlier commit's images, deploys and checks them.

## Consequences

- A merge reaches production in minutes, without anyone logging into the server, and the run on GitHub says whether it worked and which commit is live.
- Every version is tried on a real deploy (HTTPS, proxy, deployed database) before production.
- **Staging must exist before this is merged**: the first run after the merge deploys to staging, and a staging that can't be reached stops production from updating.
- About five more containers on the shared server (staging's API, web, worker, Postgres and RabbitMQ), within the same limits.
- The worker has no HTTP endpoint, so the checks don't prove it runs the new commit; it logs the commit at startup, and the Phase 5 observability work can watch it.
- Staging and production share nothing, so a schema change still has to be applied by hand on both until migrations exist ([ADR 0002](0002-sqlalchemy-and-schema-creation.md)).
- Moving tags mean the compose files don't say which commit is live; `/version`, `/api/health` and the GitHub deployment history do.
