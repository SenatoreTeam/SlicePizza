# Phase 4 — Deploying

After [the pipeline](./pipeline.md) publishes a version's images, it deploys
them: **staging first, production only if staging worked**. This page explains
how; the reasoning is in
[ADR 0009](../../../docs/adr/0009-staging-then-production.md), and the server
setup in [DEPLOY.md](../../../docs/DEPLOY.md#staging).

## Two environments

| | Staging | Production |
|---|---|---|
| Address | `staging.slicepizza.senatore.tech` | `slicepizza.senatore.tech` |
| Who uses it | The pipeline, and anyone trying a change for real | Customers and the kitchen |
| Image tag | `staging` | `latest` |
| Data | Test orders only | Real orders |
| Telegram | None (the worker logs the messages) | The pizzeria's bot |

Both run the same images from the same compose file
([`infra/dokploy/docker-compose.yml`](../../../infra/dokploy/docker-compose.yml)),
each with its own database, queue and secrets.

## From merge to production

```
images sha-<commit> published
   │
   ├─► :staging moves to sha-<commit>  ─► staging webhook ─► Dokploy deploys
   │     wait until staging reports <commit>, then place an order and
   │     move it along on the kitchen board
   │
   └─► only if that passed:
       :latest moves to sha-<commit>   ─► production webhook ─► Dokploy deploys
         wait until production reports <commit>, then read-only checks
```

- **Moving a tag rebuilds nothing.** Production gets the exact images that just
  worked on staging.
- **The deploy webhook** is a secret URL Dokploy gives each service. It can only
  redeploy that service, so it is a much smaller secret than a server password
  or an SSH key. It lives in a GitHub **environment** (`staging`, `production`),
  only readable by the jobs that deploy there.
- **The checks** wait (up to 10 minutes) until `/version` and `/api/health`
  report the new commit: a deploy takes a little while, and the old version
  answers meanwhile. Then they check the site, the menu and that the private
  routes stay private. Only staging gets an order placed on it; production is
  never written to.
- **A failed stage stops the line.** If staging fails, production keeps the
  version it has, and the run on GitHub shows what went wrong.

## Rolling back

If a version misbehaves in production anyway, the **Roll back production**
workflow (Actions tab → Run workflow) takes the commit of an earlier good version,
points `latest` back at its images, deploys and checks them. Then fix or revert
the change before merging anything else, since the next merge deploys forward
again.

## Where to look

- The pipeline run on `main` ends with **deploy (staging)** and **deploy
  (production)**, each with a link to its environment.
- **Deployments** on the repository's GitHub page lists what was deployed to
  each environment, and when.
- `https://slicepizza.senatore.tech/version` says which commit is live.
