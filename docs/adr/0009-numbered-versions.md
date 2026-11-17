# 0009: Numbered versions: production runs the newest release, and the server fetches it

- **Status:** Accepted. Its `VERSION` and `CHANGELOG.md` files: superseded by [0010](0010-releases-file.md) (`releases.toml`)
- **Date:** 2026-11-17
- **Phase:** 4

## Context

After [ADR 0008](0008-one-gated-pipeline.md), only tested commits become images. But then:

- On `main` the pipeline published `latest`, and the server deployed **every merge** within 5 minutes. Production ran "whatever `main` is now", and the only name a version had was its commit.
- `latest` says nothing about what runs: it moves with every merge, the server's configuration doesn't say which version is live, and going back means digging for a commit.
- The server is shared and run by its administrator. Its control panel (Dokploy) is reachable only from inside the server's own network, on purpose: a key to the panel controls every project on the server. **Nothing on GitHub can call the server**: no webhook, no SSH, no panel API.
- The administrator's other projects already use numbered versions, with releases the pipeline creates by itself.

## Options considered

What marks a version:

1. **Keep `latest`, every merge goes to production.** Nothing to do, but no version names, and every merge changes production.
2. **Releases created by hand** in GitHub's Releases tab, and a workflow that tags the images. Nothing in the repository says which version comes next or what it changes, and someone has to remember to do it.
3. **The version in the repository**: a `VERSION` file and a `CHANGELOG.md`, changed in the Pull Request and reviewed like the code. The pipeline tags the images and creates the release when a merge raises the version.

How the server learns about a new version:

- **GitHub tells the server** (a deploy webhook, SSH, the panel's API): needs the panel on the internet or a key to the server on GitHub. Ruled out above.
- **The server looks in GHCR**: needs nothing, the images are public.

## Decision

Option 3, and the server fetches the versions.

```
PR raises VERSION to 1.4.3 and adds its CHANGELOG.md section ──► reviewed, merged
pipeline on main: lint ─► tests ─► images sha-<commit> ─► pipeline passed
release job: slicepizza-{api,web,worker}:1.4.3 ─► same images (nothing rebuilt)
             GitHub release v1.4.3, with the CHANGELOG.md notes
                                      │
server, every 2 minutes ◄─────────────┘  newer version, all three images there?
  backup ─► compose set to :1.4.3 ─► deploy ─► checks ─► fails? previous version back
```

- **`VERSION`** holds `MAJOR.MINOR.PATCH` ([Semantic Versioning](https://semver.org/)); **`CHANGELOG.md`** has a section per version, newest first. The lint checks that they agree, and on a Pull Request that the version is not lower than `main`'s; its notice says whether merging releases a version.
- **The `release` job** runs on `main` after "pipeline passed". When `VERSION` has no images yet, it puts the version's tag on the three images the run just tested and creates the release `vX.Y.Z` with that section as its notes. The tag goes on the **first** image of each version and never moves: the Monday rebuild and later merges that keep `VERSION` don't touch it.
- **No `latest`.** Images of `main` are `sha-<commit>`; the images of a version also carry `X.Y.Z`.
- **The server's compose names the version** (`slicepizza-api:1.4.3`, and `-web`, `-worker`). Every 2 minutes the server looks in GHCR for a higher version whose three images exist. It then backs up the database, writes the new version in the compose, deploys, and checks that the containers run those images, are healthy, and that `/api/health` and `/version` answer with the version's commit. If anything fails, it puts the previous version back and does not try that version again. It never goes to a lower version by itself.

## Consequences

- The version is visible everywhere: the image tag, the server's compose, the GitHub release and its notes.
- Production changes only when a version is released. Several merges can go out together in one version, and a merge that only changes docs or tests doesn't restart anything.
- A Pull Request has to raise `VERSION` to reach production. If it doesn't, the change waits on `main` until the next version (the lint's notice says so on every Pull Request).
- The base image security fixes of the Monday rebuild reach production with the next version, not by themselves: release a PATCH version after a Dependabot update of a base image, or now and then.
- To go back, revert the change and release it as a new version. The server's administrator can also hold production at an earlier version.
- GitHub doesn't see the deploy: the server checks it and goes back by itself; `/version`, `/api/health` and the server's monitoring show what runs.
- `/version` and `/api/health` still report the commit. The release says which commit each version is, and each image carries it in its `org.opencontainers.image.revision` label.
