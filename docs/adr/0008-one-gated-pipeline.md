# 0008: One pipeline: lint, then tests, then images, and only tested commits are published

- **Status:** Accepted
- **Date:** 2026-11-15
- **Phase:** 4

## Context

By the end of Phase 3, GitHub Actions already ran the tests (`ci.yml`) and built the images (`api-image.yml`, `web-image.yml`, `worker-image.yml`). But they were **separate workflows that didn't wait for each other**:

- On a merge into `main`, the image workflows published `:latest` at the same time as the tests ran. A commit whose tests failed still became the image the server pulls within 5 minutes.
- Branch protection on `main` required a review but **no status check**, so a Pull Request with red tests could be merged.
- Nothing checked the code before the tests: an unused import, an undefined name in a rarely-run branch or a shell script quoting mistake only showed up in production, if at all.
- Each image only rebuilt when its own folder changed, so the three images on the server could come from three different commits, and nothing in a running container said which commit it was.

The roadmap asks for "lint → tests → image build" and for every change to be tested before production.

## Options considered

1. **Keep separate workflows and make the image workflows wait** (`workflow_run` on the CI workflow): fewer edits, but `workflow_run` runs the workflow from the default branch, can't easily tell which images a PR touched, and shows up as a separate run that is hard to follow.
2. **One workflow, with jobs that depend on each other** (`needs:`): lint, then the tests, then the three images, then one summary check. Every PR and every merge shows one run with the whole story.
3. **A different CI system** (a self-hosted runner, Dokploy's build from Git): builds closer to the server, but tests and images in two places, and a second system to learn and secure.

For linting:

- **ruff** for Python: one fast tool that replaces flake8, isort and pyupgrade, configured in one file for the API, the worker and the CI scripts.
- **shellcheck** for the shell scripts: it comes installed on GitHub's runners.
- A formatter (`ruff format`, black): would rewrite about 30 files today and turns reviews into style discussions. Left out for now.

## Decision

Option 2, with ruff and shellcheck.

```
lint ──► tests ─────┐   API on SQLite and Postgres, worker with RabbitMQ,
                    │   Telegram end to end, docker compose smoke test
lock files ─────────┴─► images (api, web, worker) ──► pipeline passed
```

- **`ci.yml` is the pipeline** ("Pipeline" in the Actions tab). The tests wait for the lint; the images wait for the lint, the lock-file check and every test. The old image workflows are gone; their steps stay in the reusable `build-image.yml`.
- **On a Pull Request** the images are built but not published, to prove they build. **On `main`** they are published as `sha-<commit>` and `latest`. A manual run on another branch never publishes.
- **All three images are built on every run**, from the same commit. With the layer cache, an unchanged image takes seconds, and the server never runs a mix of commits.
- **Every image knows its commit**: the pipeline passes `GIT_COMMIT` as a build argument. The API reports it in `/health` (`"version"`), the web image answers it at `/version`, and the worker logs it at startup. The smoke test checks all three.
- **Runs on `main` go one at a time**, so an older run can never publish `latest` after a newer one.
- **Every Monday the pipeline runs on `main`** and republishes all the images, so the base images' security fixes (published under the same tag) reach the server. This replaces the web image's weekly rebuild and now covers the API and the worker too: their lock files pin exact versions with hashes, so a rebuild can't pull in a new Python package.
- **ruff** is configured in `ruff.toml` at the root (errors, likely bugs, import order and outdated syntax; no style rules a formatter would own) and pinned exactly in the dev lock files, so a new ruff that adds checks arrives as its own Dependabot PR.
- **One summary check, `pipeline passed`**, is green only when every job is. It is the check branch protection requires: new jobs never need a settings change.

## Consequences

- A red test now **blocks the release**: nothing reaches GHCR, and the server keeps running the last good version.
- Image builds start after the tests (a few minutes later than before on a PR). That is the order the roadmap asks for, and it saves building images for commits that fail anyway.
- `sha-<commit>` tags exist for every image at every commit on `main`, so a deploy can put one exact version on a staging environment and then in production.
- The weekly rebuild republishes `sha-<commit>` for the same commit with newer base layers. The tag still means "this commit's code"; the image digest changes.
- Developers run `ruff check .` from the repository root (ruff is in each service's `.venv` with the dev requirements), or let the pipeline tell them.
