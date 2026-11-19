# Contributing

## Workflow

1. Update `main`: `git checkout main && git pull`
2. Create a branch for your task: `git checkout -b feat/create-order`
3. Make small commits with clear messages.
4. Push the branch: `git push -u origin feat/create-order`
5. Open a Pull Request on GitHub and ask for a review.
6. Once approved, merge it and delete the branch.

**Never push directly to `main`.**

Every Pull Request runs the [pipeline](.github/workflows/ci.yml): lint, tests, then the images. Merge only when its **pipeline passed** check is green: on `main`, a red pipeline means nothing is published ([ADR 0008](docs/adr/0008-one-gated-pipeline.md)).

A merge reaches production only when it adds a version at the top of [`releases.toml`](releases.toml) (and the README's **Current version** line): the pipeline then publishes that version and the server installs it ([ADR 0009](docs/adr/0009-numbered-versions.md), [ADR 0010](docs/adr/0010-releases-file.md), [Releasing a version](docs/DEPLOY.md#releasing-a-version)).

## Branch names

| Prefix | When to use | Example |
|---|---|---|
| `feat/` | New feature | `feat/create-order` |
| `fix/` | Bug fix | `fix/invalid-status` |
| `docs/` | Documentation only | `docs/adr-rabbitmq` |
| `infra/` | Docker, backups, CI/CD | `infra/api-pipeline` |

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
feat(api): add POST /orders route
fix(api): reject invalid order status
docs: add ADR about RabbitMQ
infra: add Postgres to docker-compose
```

## Before opening a Pull Request

- [ ] `docker compose up --build` runs without errors (from Phase 1 on)
- [ ] Tests pass (from Phase 1 on)
- [ ] `ruff check .` passes, from the repository root (from Phase 4 on)
- [ ] No secrets (passwords, tokens, keys) were committed
- [ ] A new version at the top of `releases.toml` and in the README's **Current version** line, if the change should reach production (Dependabot's updates with `source = "dependabot"` and `pr`)
- [ ] Documentation updated, if the change affects how to run or use the system
- [ ] [ROADMAP](docs/ROADMAP.md) boxes checked, if the task was listed there
