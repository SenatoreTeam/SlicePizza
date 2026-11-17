# Phase 4 — Versions and releases

Production runs **numbered versions**, never "whatever `main` is now": a merge
reaches production only when it adds a version. This page explains how
versions are numbered, where they are written and where they show; the
reasoning is in [ADR 0009](../../../docs/adr/0009-numbered-versions.md) and
[ADR 0010](../../../docs/adr/0010-releases-file.md), and the server's side in
[DEPLOY.md](../../../docs/DEPLOY.md#releasing-a-version).

## The number: `MAJOR.MINOR.PATCH`

[Semantic Versioning](https://semver.org/):

| Part | When it goes up | Example |
|---|---|---|
| **MAJOR** | Something that worked now works differently: a route or an event's format changes, or the database needs a change by hand | 1.4.2 → **2.0.0** |
| **MINOR** | Something new, and everything that worked keeps working: a new route, a new page, a new message | 1.4.2 → **1.5.0** |
| **PATCH** | A fix, or a base image or dependency update, with nothing new for the people who use it | 1.4.2 → **1.4.3** |

When MINOR goes up, PATCH goes back to zero; when MAJOR goes up, both do.

## Where it is written: `releases.toml`

[`releases.toml`](../../../releases.toml), at the root of the repository, is the
**single source** of the versions. A new version goes at the **top**:

```toml
[[release]]
version = "1.5.0"
date = 2026-12-01
title.en = "Pizzas can be marked as sold out"          # optional, one sentence
title.pt-br = "Pizzas podem ser marcadas como esgotadas"

[[release.item]]
kind = "new"                   # new | improvement | fix | security
area = "Menu"                  # Menu | Orders | Kitchen | Telegram | System
text.en = "The kitchen can mark a pizza as sold out, and the menu hides it until it is back."
text.pt-br = "A cozinha pode marcar uma pizza como esgotada, e o cardápio a esconde até ela voltar."

[[release.item]]
kind = "security"
area = "System"
source = "dependabot"          # proposed by Dependabot, with its Pull Request
pr = 52
text.en = "Libraries updated, with security fixes."
text.pt-br = "Bibliotecas atualizadas, com correções de segurança."
```

- One item per change, **in the words of the people who use the system**: "The
  menu hides sold-out pizzas", not "Added a sold_out column".
- Texts in English and Portuguese. The GitHub release and the pages use the
  English ones.
- Dependabot's updates have `source = "dependabot"` and their `pr`, so the
  project's own changes and Dependabot's are told apart.
- A security fix says that something was fixed, never how to exploit it.
- The README's `**Current version:**` line says the same version.

The lint checks all of it: the format, the kinds and areas, both languages,
newest first with each version higher than the one below, the dates, and the
README line. On a Pull Request it also says, in a notice, whether merging
releases a version.

## From merge to production

```
PR adds 1.5.0 at the top of releases.toml ──► reviewed, merged
pipeline on main: lint ─► tests ─► images sha-<commit> ─► pipeline passed
release job: slicepizza-{api,web,worker}:1.5.0 (the same images, nothing rebuilt)
             GitHub release v1.5.0: "1.5.0 – Pizzas can be marked as sold out"
                                   - **New · Menu:** The kitchen can mark…
                                   │
server, every 2 minutes ◄──────────┘  backup ─► :1.5.0 ─► deploy ─► checks
                                   │
production check (GitHub) ◄────────┘  waits for 1.5.0 on the site, then checks it, read-only
```

The pipeline run ends with **production check**: green when production answers
with the new version and passes the checks, red when it doesn't within 15
minutes ([ADR 0011](../../../docs/adr/0011-production-check.md)). The server
only goes forward when its own checks pass, so red means "not live yet", not
"production is broken".

A merge that adds no version changes nothing in production: several merges can
go out together in one version.

## Where it shows

| Where | What |
|---|---|
| The menu site | "Version 1.5.0 · what changed" at the bottom, linking to its GitHub release |
| The kitchen board | The version at the bottom, and **What's new**: every version with its items. After an update, a notice says a new version is live until What's new is opened in that browser |
| `/api/health` | `release` (the version) and `version` (the commit) |
| `/api/docs` | The version, next to the API's name |
| The worker's log | `Starting version 1.5.0 (commit …)` when it starts |
| GitHub | The [releases](https://github.com/SenatoreTeam/SlicePizza/releases), one per version, the images' tags on GHCR, the **production check** of the run that released it, and **Deployments** (each version that went live) |

The pages read `/releases.json`, which the web image makes from `releases.toml`
when it is built; the API and the worker get the version from the pipeline.
