# Phase 4 — The pipeline

Every Pull Request and every merge into `main` runs one GitHub Actions workflow,
the **Pipeline** ([`ci.yml`](../../../.github/workflows/ci.yml)). This page
explains its stages and why they are in this order; the reasoning is in
[ADR 0008](../../../docs/adr/0008-one-gated-pipeline.md).

## The stages

```
lint ──► tests ─────┐   API on SQLite and Postgres, worker with RabbitMQ,
                    │   Telegram end to end, docker compose smoke test
lock files ─────────┴─► images (api, web, worker) ──► pipeline passed
```

1. **Lint.** [ruff](https://docs.astral.sh/ruff/) reads the Python code
   (API, worker and CI scripts) and shellcheck the shell scripts, looking for
   mistakes a machine can spot without running anything: an unused import, a
   name that doesn't exist, an exception swallowed by accident. It takes
   seconds, so it runs first.
2. **Tests**, all in parallel: the API's tests on SQLite and on a real Postgres,
   the worker's tests with a real RabbitMQ, a customer following an order on
   Telegram end to end, and the whole stack started with `docker compose`.
   Next to them, a check that the lock files match their `.in` files.
3. **Images.** Only when everything above passed are the three images built:
   `api`, `web` and `worker`, all from the same commit.
4. **pipeline passed**: one last check that is green only if every stage was.
   It is the check branch protection asks for, so a Pull Request with a red
   stage can't be merged.

## Pull Request or main

| | Pull Request | `main` |
|---|---|---|
| Lint and tests | Run | Run |
| Images | Built, to prove they build | Built **and published** to GHCR |
| Tags | — | `sha-<commit>` and `latest` |

A merge whose pipeline fails publishes nothing, and the server keeps running the
last good version. Runs on `main` go one at a time, so an older run can never
publish `latest` after a newer one.

Every Monday the pipeline also runs on `main` by itself and republishes the
images, so the security fixes that the official Python and Caddy images get
under the same tag reach the server.

## Which version is running?

The pipeline builds each image with the commit it came from (`GIT_COMMIT`):

- the API reports it in `/api/health`:
  `{"status":"ok","database":"ok","version":"<commit>"}`
- the web container answers it at `/version`
- the worker writes it in its first log line: `Starting version <commit> ...`

Built on your machine, they say `unknown`. The deploy uses this to check that
the version it just shipped is the one answering.

## Running the lint yourself

ruff is installed with the dev requirements of the API and of the worker. From
the repository root:

```bash
ruff check .          # what the pipeline runs
ruff check --fix .    # fix what it can (import order, old syntax...)
```

The rules are in [`ruff.toml`](../../../ruff.toml). They look for likely bugs,
not style: there is no formatter to argue with.
