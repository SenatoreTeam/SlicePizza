# Changelog

Every version of SlicePizza, newest first. Production runs the newest version
([ADR 0009](docs/adr/0009-numbered-versions.md)):

1. A Pull Request that should reach production raises [`VERSION`](VERSION) and adds its
   section at the top of this file, with what changes for the people who use the system.
2. When it is merged and the pipeline passes, the pipeline tags the images it just tested
   with the version (`slicepizza-api:1.4.2`, and the same for `-web` and `-worker`) and
   creates the GitHub release `v1.4.2` with the section below as its notes.
3. The server sees the new version and puts it in production by itself.

A Pull Request that keeps `VERSION` changes nothing in production. How to choose the
number and what happens on the server: [Releasing a version](docs/DEPLOY.md#releasing-a-version).

## [1.0.0] - 2026-11-17

The first numbered version: the system that is already live.

- The menu site at `/` and the Orders API at `/api`, on one domain.
- Order events through RabbitMQ, and Telegram messages for the pizzeria and for the customers who follow their order.
- The kitchen board at `/kitchen`, behind a login.
- One gated pipeline: lint, tests, then images.
- Numbered versions: the server now runs the newest released version, instead of every merge into `main`.
