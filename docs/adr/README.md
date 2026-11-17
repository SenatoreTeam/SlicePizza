# ADRs: Architecture Decision Records

An ADR (*Architecture Decision Record*) is a short document that records **an important decision and why it was made**. Six months from now, nobody will remember why we picked RabbitMQ over Redis. The ADR will.

## How to write an ADR

1. Copy the [template](0000-template.md) to a new file with the next number: `0002-short-title.md`.
2. Fill in the sections. Half a page is enough.
3. Add a row to the table below.
4. Open a Pull Request.

An accepted ADR is not edited. If the decision changes, write a new ADR and mark the old one as "Superseded by 00XX".

## ADR list

| No. | Title | Status |
|---|---|---|
| [0001](0001-monorepo.md) | Use a single repository (monorepo) | Accepted |
| [0002](0002-sqlalchemy-and-schema-creation.md) | SQLAlchemy ORM and schema creation on startup | Accepted |
| [0003](0003-one-domain-caddy-in-front.md) | One domain for the site and the API, with Caddy in front | Accepted |
| [0004](0004-order-events-outbox-rabbitmq.md) | Order events through a transactional outbox and RabbitMQ | Accepted |
| [0005](0005-notification-worker.md) | The notification worker: one queue, retries, dead letters | Accepted |
| [0006](0006-customer-telegram-opt-in.md) | Customers follow their order on Telegram, linked through the API | Accepted |
| [0007](0007-kitchen-login.md) | The kitchen board at /kitchen, behind a Caddy login and a token | Accepted |
| [0008](0008-one-gated-pipeline.md) | One pipeline: lint, then tests, then images, and only tested commits are published | Accepted |
| [0009](0009-numbered-versions.md) | Numbered versions: production runs the newest release, and the server fetches it | Accepted (its files superseded by 0010) |
| [0010](0010-releases-file.md) | The versions live in releases.toml, like the other projects | Accepted |
| [0011](0011-production-check.md) | The pipeline checks each new version in production, from the outside | Accepted |
| [0012](0012-api-metrics.md) | The API reports its own metrics, with no new dependency | Accepted |
| [0013](0013-prometheus-and-grafana.md) | Prometheus and Grafana, on the same server, from files in Git | Accepted |
