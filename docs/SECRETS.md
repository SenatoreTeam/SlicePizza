# Secrets and credentials

Every password, token and key the project uses: what it protects, where it lives, how much power it has, and how to replace it. **None is in Git** (`.env` is ignored, and the whole history is scanned in CI: [ADR 0021](adr/0021-hardening.md)). Values never go in an issue, a PR, a chat or a log.

Rotate **right away** if one is ever seen where it should not be (a screenshot, a log, a commit), and **on a routine** at least once a year, and whenever someone who knew it leaves the project.

## Inventory

| Credential | Protects | Lives in | Power | Rotation |
|---|---|---|---|---|
| `POSTGRES_PASSWORD` | The database: customers, orders | Server `.env` (the API and Postgres containers) | Everything in the database | New value in the server `.env`, **and** in Postgres: `ALTER USER slicepizza PASSWORD '...'` (the container only reads it on first boot). Then restart `api`. Orders wait in the outbox meanwhile; nothing is lost |
| `RABBITMQ_PASSWORD` | The message queue | Server `.env` (API, worker, RabbitMQ) | Read and write every queue | `rabbitmqctl change_password`, then the new value in `.env` for the API and worker, and restart both. Events wait in the outbox meanwhile |
| `INTERNAL_API_TOKEN` | The `/internal` routes the worker calls (link a customer's Telegram chat to an order) | Server `.env` (API and worker) | Link chats to orders | `openssl rand -hex 32`, set on both, restart both. Not reachable from the internet (`/api/internal` is checked by the production check) |
| `KITCHEN_API_TOKEN` | Listing orders and changing their status; signs the kitchen's sessions (ADR 0024) | Server `.env` (API and web); the browser never sees it | The kitchen's power over orders | `openssl rand -hex 32`, set on both, restart both. Logs every kitchen device out |
| Kitchen password (`KITCHEN_PASSWORD_HASH` holds its bcrypt hash) | The kitchen board's login (checked by the API) | The people who use it; the hash in the server `.env` (web) | The kitchen's power over orders | New password through `caddy hash-password` ([DEPLOY.md](DEPLOY.md#kitchen)), new hash in `.env`, restart `web`. Logs every device out. Tell the kitchen |
| `TELEGRAM_BOT_TOKEN` | The pizzeria's bot: messages to customers and the kitchen chat | Server `.env` (the worker) | Send as the bot, read its messages | `/revoke` in BotFather gives a new token; set it, restart `worker`. The old token stops working at once |
| `TELEGRAM_PIZZERIA_CHAT_ID`, `TELEGRAM_BOT_USERNAME` | Not secrets | `.env` | None on their own | n/a |
| `GITHUB_TOKEN` (CI) | Pipeline: read the code, publish images, make releases | Created by GitHub for each run, gone after it | `contents: read` by default; `packages: write` to publish; `contents: write` only in the release job | Nothing to rotate. Keep the `permissions:` blocks as small as they are |
| Dependabot | Opens update PRs | GitHub | Opens PRs; the pipeline checks them | n/a |
| GHCR packages | Image pulls by the server | Public packages (no pull credential on the server) | Anyone can pull the images: they contain no secret (scanned) | n/a |
| Server's access (SSH keys, Dokploy login, Cloudflare account, registry) | The VPS and the domain | The server's owner | Everything on the server | Server owner's own routine; see below |
| `GRAFANA_ADMIN_PASSWORD`, `ALERT_TELEGRAM_*` | Removed with this repository's monitoring ([ADR 0016](adr/0016-server-monitoring.md)) | n/a | n/a | If they exist on the server from the earlier plan, delete them |

## Review (Phase 8, 2026-11-19)

- **In Git:** the history was scanned (Gitleaks, 152 commits): no real secret. The matches were a test's made-up token and Grafana's default `admin:admin` used against a throwaway container in CI; both are listed in `.gitleaks.toml` with a reason. The scan now runs on every change.
- **In the images:** Trivy scans every image for HIGH and CRITICAL vulnerabilities with a fix, and for secrets, before anything is published ([ADR 0021](adr/0021-hardening.md)).
- **In CI:** every job has `contents: read`; only the image build can write packages and only the release job can write contents. No long-lived token is stored in GitHub for deploying: the server pulls versions by itself ([ADR 0009](adr/0009-numbered-versions.md)).
- **Generation:** tokens are `openssl rand -hex 32` (256 bits); the kitchen password is stored as a bcrypt hash with cost 14.
- **Containers run as non-root:** `api`, `worker`, `web` and (now) `redis`. Postgres and RabbitMQ start as root only to fix their data folders and then drop to their own user: that is how the official images work.
- **Not verified from this repository** (the server is the owner's): that the server's `.env` is readable only by its owner, that SSH uses keys and no password, that Dokploy has a strong password and two-step login, that Cloudflare's account has two-step login, and that the server's backups are encrypted. Ask the server's owner to confirm each and note the date here.
- **Left as it is (then):** the kitchen login had no attempt limit. **Fixed in ADR 0024 (2026-11-26):** 5 wrong passwords lock the address for 15 minutes, and a session ends after 12 hours.
