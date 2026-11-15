# Phase 4 — Overview

**Zé's request:** _"Every time you change something, something breaks."_

By the end of Phase 3 there were four services and several secrets, all updated
by merging to `main`. The tests ran on every Pull Request, but nothing stopped a
merge with red tests, and the images were published at the same time as the
tests ran, not after. Phase 4 makes the path from a merge to production
automatic **and** safe.

:::info Status
This phase is **in progress**: the pipeline and the deploy are built, and go
live once the staging environment is set up on the server. See the
[roadmap](../../../docs/ROADMAP.md).
:::

## What Phase 4 delivers

- **One pipeline** for every change: lint, then the tests, then the images. An
  image is published only when everything before it passed. See
  [The pipeline](./pipeline.md).
- **Versioned images**: every image says which commit it was built from.
- A **staging** environment at `staging.slicepizza.senatore.tech`, and a
  deploy that the pipeline starts and checks, first on staging and then in
  production, with its secrets in GitHub. See [Deploying](./deploy.md).

## Why automate this

Checking by hand works while one person changes one thing at a time. With several
people, several services and Dependabot opening Pull Requests every week, a
human eventually forgets a step. A pipeline runs the same checks every time, in
the same order, and refuses to ship what fails them.
