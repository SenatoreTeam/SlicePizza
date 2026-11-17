# 0011: The pipeline checks each new version in production, from the outside

- **Status:** Accepted
- **Date:** 2026-11-17
- **Phase:** 4

## Context

Since [ADR 0009](0009-numbered-versions.md), a merge that adds a version to `releases.toml` publishes it, and the server installs it by itself: it backs up the database, deploys, checks the containers and the commit the site answers with, and puts the previous version back if anything fails. But **nothing on GitHub says whether the version went live**. The pipeline run ends green at `release`, whatever happens on the server afterwards; finding out meant asking the server's administrator or opening the monitoring dashboard.

The first plan for this part of Phase 4 (Pull Request #43) deployed from GitHub: a staging environment first, then production, each through Dokploy's deploy webhook, with the webhooks in GitHub environments. That can't work here, and was dropped:

- the server's control panel (Dokploy) is reachable only from inside the server's network, so GitHub can't call its webhook;
- there is no staging environment: each version goes straight to production, protected by the server's checks and its automatic rollback ([ROADMAP](../ROADMAP.md)).

What stays useful from that plan is its check script: wait until the new version answers, then check what any visitor sees.

## Options considered

1. **Nothing on GitHub.** The server's checks and the dashboard are enough for the administrator, but whoever merged doesn't see the result where they work.
2. **The server reports to GitHub** (a commit status or a deployment through GitHub's API). Exact, but the server would need a GitHub token with write access to the repository.
3. **The pipeline watches the public site.** After `release` publishes a new version, a job waits until `/api/health` and `/version` answer with the version's commit and `/api/health` and `/releases.json` with its number, then runs the read-only checks. No secret and no access to the server: it sees what a customer sees.

## Decision

Option 3: a **production check** job at the end of the pipeline.

```
release ──(a new version was published)──► production check
             server installs it (≤ a few minutes)    │ waits up to 15 minutes for
                                                     │ commit + version, then checks
                                                     ▼
                                    green: live and checked · red: not live
```

- **`release.sh`** writes `published=true` only when that run tagged the images of a new version, and the version number; the job runs only then (not for merges that add no version, nor on the Monday rebuild).
- **`check_deploy.py`** (from #43) waits up to 15 minutes until the web's `/version` and the API's `/api/health` report the commit, and `/api/health`'s `release` and `/releases.json`'s `version` report the version. Then it checks the menu site, the menu, the API docs, and that the private routes stay private (`/kitchen` asks for a login, orders can't be listed or changed without the kitchen's token, `/api/internal` is not reachable).
- **It never writes**: an order placed in production would reach the real kitchen board and the pizzeria's Telegram. #43's write checks (place an order, move it on the board) were for staging, and are gone.
- The job uses a GitHub **environment** called `production`, with no secrets, so the repository's **Deployments** page lists each version that went live.

## Consequences

- The run of a merge that releases a version says whether it went live: green, or red with what production answers instead.
- Red does not mean production is broken: the server keeps the previous version when the new one fails its checks. It means the new version is not live, and someone has to look (the dashboard shows why).
- A run that releases a version takes up to a few minutes longer: the job waits for the server's next look (every 2 minutes) and its deploy.
- The checks see only the public side. The kitchen board behind its login and the Telegram messages are covered by the tests and the smoke test before the images are published, not in production.
