# Phase 4 — Overview

**Zé's request:** _"Every time you change something, something breaks."_

By the end of Phase 3 there were four services and several secrets, all updated
by merging to `main`. The tests ran on every Pull Request, but nothing stopped a
merge with red tests, and the images were published at the same time as the
tests ran, not after. Phase 4 makes the path from a merge to production
automatic **and** safe.

:::info Status
This phase is **done**: live since 2026-11-17. A merge that adds a version to
`releases.toml` reaches production by itself, checked, without anyone logging
into the server. See the [roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 4 delivers

- **One pipeline** for every change: lint, then the tests, then the images. An
  image is published only when everything before it passed. See
  [The pipeline](./pipeline.md).
- **Numbered versions**: production runs a version (`1.1.0`), written in
  `releases.toml` and released by the pipeline when a merge adds one, never
  "whatever `main` is now". Every image says which commit it was built from, and
  the version and what changed show in the system. See
  [Versions and releases](./versions.md).
- **A checked deploy**: the server finds each new version in GHCR by itself,
  backs up the database, deploys it, checks it, and puts the previous version
  back if the checks fail. GitHub never reaches the server, so no deploy secret
  lives on GitHub.
- Not built: a **staging** environment. The checks and the automatic rollback
  protect production; staging remains an option.

## Why automate this

Checking by hand works while one person changes one thing at a time. With several
people, several services and Dependabot opening Pull Requests every week, a
human eventually forgets a step. A pipeline runs the same checks every time, in
the same order, and refuses to ship what fails them.
