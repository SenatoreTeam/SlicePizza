# Deploy

SlicePizza runs on a shared server at **`https://slicepizza.senatore.tech`**: the menu site at `/`, the Orders API at `/api` (see [ADR 0003](adr/0003-one-domain-caddy-in-front.md)). The docs site is separate, on GitHub Pages at `https://slicepizza-docs.senatore.tech`. Nobody deploys by hand: **merging a Pull Request that raises the version is the deploy** ([ADR 0009](adr/0009-numbered-versions.md)).

```
PR merged into main ──► pipeline: lint ─► tests ─► images slicepizza-{api,web,worker}:sha-<commit>
                                                        │
                     new version in releases.toml? ── no ──► nothing else: production keeps its version
                                                        │ yes
                              release: the same images tagged 1.4.3, GitHub release v1.4.3
                                                        │
                       server checks every 2 minutes ◄──┘
                       newer version? ──► backup, compose set to :1.4.3, deploy, checks
                                          (the previous version back if they fail)

https://slicepizza.senatore.tech ──► server proxy (HTTPS) ──► web:8080 (Caddy)
                                                                ├─ /        ► menu site
                                                                └─ /api/*   ► api:8000 ──► db:5432
```

- The [pipeline](../.github/workflows/ci.yml) builds the three images only after the lint and every test passed ([ADR 0008](adr/0008-one-gated-pipeline.md)). On a Pull Request it only checks that they build; nothing is published. A red pipeline on `main` publishes nothing, so production keeps its version.
- All three images are built from the same commit on every run (the steps are in [build-image.yml](../.github/workflows/build-image.yml)).
- Every Monday the pipeline runs on `main` again and republishes `main`'s `sha-<commit>` images with the security fixes the official base images (Python, Caddy) get under the same tag. A published version never changes, so those fixes reach production with the next version: see [Releasing a version](#releasing-a-version). New base versions come from Dependabot, as Pull Requests.
- Tags: every image of `main` gets `sha-<commit>`. The three images of a version also get the version, `X.Y.Z` (e.g. `slicepizza-api:1.4.3`), which never moves. There is no `latest`: the server's compose names the version it runs.
- The images belong to the `SenatoreTeam` organization, like the repository. Registry names are lowercase, hence `senatoreteam`.

## The containers

| Container | Image | Public? | Settings |
|---|---|---|---|
| `web` | `slicepizza-web` (Caddy + the site, [`infra/caddy/`](../infra/caddy/)) | **Yes**: the domain points here, port 8080 | `API_UPSTREAM`: the API's `host:port` on the project network (default `api:8000`). `TELEGRAM_BOT_USERNAME`: the bot for the "Follow on Telegram" button, without the @ (unset: no button). `KITCHEN_PASSWORD_HASH`, `KITCHEN_USERNAME` and `KITCHEN_API_TOKEN` for the kitchen board (see [Kitchen](#kitchen)). `TRUSTED_PROXIES` if the server's proxy is outside the private ranges (see below) |
| `api` | `slicepizza-api` ([`api/`](../api/)) | No: only `web` reaches it | `UVICORN_ROOT_PATH=/api` and `UVICORN_FORWARDED_ALLOW_IPS=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`, plus the database variables below. `INTERNAL_API_TOKEN` for the worker's routes ([ADR 0006](adr/0006-customer-telegram-opt-in.md)). `KITCHEN_API_TOKEN` for the kitchen's routes ([ADR 0007](adr/0007-kitchen-login.md)) |

| `db` | `postgres:16-alpine` | No: only `api` reaches it | See [Database](#database) |
| `rabbitmq` | `rabbitmq:4.4.0-management-alpine` | No: only `api` and `worker` reach it | See [RabbitMQ](#rabbitmq) |
| `worker` | `slicepizza-worker` ([`worker/`](../worker/)) | No: no port at all, it only connects out (RabbitMQ, Telegram) | `RABBITMQ_HOST`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_PIZZERIA_CHAT_ID`. See [Worker](#worker) |

Both trust the forwarding headers of the proxy in front of them: Caddy those of the server's proxy (from private addresses, see the Caddyfile), and the API those of Caddy (also from private addresses only). That way the access logs show the customer's IP, and links and redirects the API generates keep `https`.

If the server's proxy is not in a private range (on the live server Traefik is at `100.80.1.0/24`, which is not), Caddy ignores its headers and logs the proxy's IP and `http`. Set `TRUSTED_PROXIES` on `web` to the ranges to trust, space-separated and with `private_ranges` kept: `private_ranges 100.80.1.0/24`. On `api`, put the same range in `UVICORN_FORWARDED_ALLOW_IPS` (comma-separated).

Both images meet the server's rules:

| Requirement | Why | How |
|---|---|---|
| Listen on `0.0.0.0` on a port above 1024 | The proxy forwards plain HTTP to the container | `api`: Uvicorn on 8000. `web`: Caddy on 8080, with no HTTPS of its own (the server's proxy has the certificate) |
| Run as a non-root user, needing no special Linux capabilities | The containers run with all capabilities dropped and `no-new-privileges` | Both run as uid 10001. The web image removes the port-binding capability the official Caddy image gives its binary |
| Fit in 512 MB of RAM and 1 CPU | Those are each container's limits | Caddy uses a few tens of MB |
| Read settings from environment variables | Variables and secrets are set on the server, never in Git | |

`docker-compose.yml` runs the same containers with the same restrictions, so `docker compose up` on your machine behaves like the server.

`CORS_ORIGINS` (see [api/README.md](../api/README.md#calling-the-api-from-a-browser-cors)) is not needed: the site and the API share one origin. Set it only if a site on another domain must call the API from the browser.

## Database

The API **refuses to start without a database** (see `api/app/config.py`): there is no silent fallback to a local file, because that would lose orders on every redeploy. On the server it uses PostgreSQL, the same way `docker-compose.yml` does locally.

| Item | On the server |
|---|---|
| Image | `postgres:16-alpine`, the same version as `docker-compose.yml` and CI |
| Network | The project's isolated network only. **No published port**: only the API reaches it, by service name |
| Data | A named volume, so the data survives API updates. The automatic update replaces **only the `api` and `web` containers**, never the database |
| API variables | `POSTGRES_HOST` (the database service name), `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`. Passed separately, not as a URL, so the password can contain any character |
| Password | Strong, random, stored on the server. Never in Git |
| Backup | A daily `pg_dump`, kept outside the volume. Without it, losing the volume means losing every order |

On first boot the API waits for Postgres to accept connections, creates the tables and seeds the menu (see [ADR 0002](adr/0002-sqlalchemy-and-schema-creation.md)). An empty database is all it needs.

`create_all()` does not alter existing tables. Before a change to `api/app/models.py` reaches the server, the project needs migrations (Alembic, planned in ADR 0002); until then, a schema change on the server means adjusting the tables by hand.

## RabbitMQ

Order events go from the API to RabbitMQ through the outbox ([ADR 0004](adr/0004-order-events-outbox-rabbitmq.md)). The API does not depend on it: if RabbitMQ is missing or down, orders still work and their events wait in the `order_events` table.

| Item | On the server |
|---|---|
| Image | `rabbitmq:4.4.0-management-alpine`, the same as `docker-compose.yml` and CI. Once a node has run 4.4, it cannot go back to 4.3 (new classic-queue store format), so upgrade, don't downgrade |
| Hostname | **Fixed** (e.g. `rabbitmq`). RabbitMQ stores its data under `rabbit@<hostname>`: with a new random hostname after a redeploy, the queues in the volume would seem gone |
| Network | The project's network only. **No published port** and no domain: the management UI (15672) is reached through an SSH tunnel when needed |
| Data | A named volume on `/var/lib/rabbitmq`, so queued messages survive restarts. Never replaced by the automatic update |
| User | `RABBITMQ_DEFAULT_USER` / `RABBITMQ_DEFAULT_PASS` on the RabbitMQ container: a strong, random password, stored on the server. Created on first boot only |
| API variables | `RABBITMQ_HOST` (the service name), `RABBITMQ_USER`, `RABBITMQ_PASSWORD`; optionally `RABBITMQ_PORT` (5672) and `RABBITMQ_VHOST` (`/`) |

**Deploy RabbitMQ and the worker together.** Until the worker has declared its queue, events have nowhere to go: nothing is lost (they wait in `order_events`), but with `RABBITMQ_HOST` set the API logs a warning on every retry.

## Worker

The notification worker ([`worker/`](../worker/), [ADR 0005](adr/0005-notification-worker.md)) reads order events from its queue and sends Telegram messages. It has no port and no domain.

| Item | On the server |
|---|---|
| Image | `ghcr.io/senatoreteam/slicepizza-worker:<version>`, updated to each new version like the others |
| Network | The project's network, to reach `rabbitmq` and `api`. It also needs outgoing HTTPS to `api.telegram.org` |
| Variables | `RABBITMQ_HOST`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD` (the same user as the API), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_PIZZERIA_CHAT_ID`, `API_URL` (the API on the project network, e.g. `http://api:8000`) and `INTERNAL_API_TOKEN` (**the same value as on the API**) |
| Instances | **Exactly one.** It reads the bot's messages by long polling, and Telegram allows one reader per bot: a second worker would get 409 Conflict ([ADR 0006](adr/0006-customer-telegram-opt-in.md)) |
| Secrets | The bot token is a password: stored on the server only, never in Git |
| Health | Healthy while `/tmp/worker-alive` is less than 30 s old (see `docker-compose.yml`) |
| Restarts | Safe at any time: a message is acknowledged only after it was sent; an interrupted one goes back to the queue |

How to create the bot and find the chat id: [worker/README.md](../worker/README.md#setting-up-telegram). Without `TELEGRAM_BOT_TOKEN` the worker writes the messages to its log instead of sending them. That is meant for local development and CI: the messages include customers' names, so on the server set the token when you deploy the worker (or accept names in the logs until you do).

## Releasing a version

Production runs the newest version ([ADR 0009](adr/0009-numbered-versions.md)), and the versions live in [`releases.toml`](../releases.toml) ([ADR 0010](adr/0010-releases-file.md)). To release one, in the Pull Request:

1. Add a `[[release]]` block at the **top** of `releases.toml`, with a version higher than the one below, following [Semantic Versioning](https://semver.org/):
   - **PATCH** (1.4.2 → 1.4.3): fixes, and base image or dependency updates, with nothing new for the people who use it.
   - **MINOR** (1.4.2 → 1.5.0): something new, and everything that worked keeps working (a new route, a new page, a new message).
   - **MAJOR** (1.4.2 → 2.0.0): something that worked now works differently (a route or an event's format changes, or the database needs a change by hand).
2. Under it, one `[[release.item]]` per change: its `kind` (`new`, `improvement`, `fix` or `security`), its `area` (`Menu`, `Orders`, `Kitchen`, `Telegram` or `System`) and its text in English and Portuguese (`text.en`, `text.pt-br`), written for the people who use the system. An update proposed by Dependabot adds `source = "dependabot"` and `pr = <its number>`. The comment at the top of the file has a complete example.
3. Change the `**Current version:**` line of the [README](../README.md) to the new version.

```toml
[[release]]
version = "1.4.3"
date = 2026-11-20
title.en = "Orders can't be placed with an empty cart"
title.pt-br = "Não dá mais para fazer pedido com o carrinho vazio"

[[release.item]]
kind = "fix"
area = "Orders"
text.en = "Placing an order with no pizzas now shows an error instead of creating an empty order."
text.pt-br = "Fazer um pedido sem pizzas agora mostra um erro, em vez de criar um pedido vazio."
```

The lint checks the file and the README line, and refuses a version lower than `main`'s; its notice on the Pull Request says whether merging releases a version. After the merge, once the pipeline passed, its **release** job tags the images it just tested with the version and creates the release `v1.4.3` on [GitHub](https://github.com/SenatoreTeam/SlicePizza/releases), titled `1.4.3 – Orders can't be placed with an empty cart`, with one line per item (`- **Fix · Orders:** …`, and `(Dependabot, #N)` on Dependabot's). Then, within a few minutes, the server:

1. sees the new version in GHCR (it looks every 2 minutes, and only takes a version whose three images exist);
2. backs up the database;
3. writes the version in its compose (`slicepizza-api:1.4.3`, and the same for `-web` and `-worker`) and deploys it;
4. checks that the containers run those images and are healthy, and that `/api/health` and `/version` answer with the version's commit;
5. if any of that fails, puts the previous version back and doesn't try that version again: release the fix as a new version.

A merge that adds no version is published as `sha-<commit>` only, and production doesn't change: several merges can go out together in one version. The server never goes to a lower version by itself: to go back, revert the change and release it as a new version (e.g. 1.4.4 with 1.4.2's code). In an emergency the server's administrator can hold production at an earlier version.

## Checking the deploy

- `https://slicepizza.senatore.tech/` shows the menu, and placing an order from a phone works end to end.
- `https://slicepizza.senatore.tech/api/health` answers when the API is up and connected to the database. (Before ADR 0003 this was `/health`; update any monitor that still checks the old address.)
- `https://slicepizza.senatore.tech/api/docs` shows the API's interactive docs.
- `https://slicepizza.senatore.tech/version` (the web image) and the `version` in `/api/health` (the API) show the commit each one was built from; the worker logs its commit when it starts (`Starting version ...`). The [release](https://github.com/SenatoreTeam/SlicePizza/releases) of the version running (the tag of each image in the server's compose, e.g. `1.4.3`) names the same commit.

## Kitchen

The kitchen board is at `https://slicepizza.senatore.tech/kitchen/`, behind a login ([ADR 0007](adr/0007-kitchen-login.md)). It needs three settings:

| Setting | On | Value |
|---|---|---|
| `KITCHEN_API_TOKEN` | `api` **and** `web`, the same value | `openssl rand -hex 32` |
| `KITCHEN_PASSWORD_HASH` | `web` | The login's password, hashed and base64-encoded (below) |
| `KITCHEN_USERNAME` | `web` | Optional, default `kitchen` |

To make the hash, run this on any machine with Docker. It asks for the password twice and prints the value:

```bash
docker run --rm -it caddy:2.11.8-alpine sh -c 'caddy hash-password | base64 -w0; echo'
```

Only the hash goes on the server; keep the password in the team's password manager. Use a long one: the login is the only thing between the internet and customers' phone numbers and addresses.

What happens when something is missing:

- **No `KITCHEN_PASSWORD_HASH`**: `/kitchen` answers 404.
- **A malformed `KITCHEN_PASSWORD_HASH`** (cut short when pasting, say): `/kitchen` answers 404 too, and the `web` log starts with an `ERROR: KITCHEN_PASSWORD_HASH ...` line. The rest of the site keeps working: the image checks the value before Caddy loads it ([`infra/caddy/start.sh`](../infra/caddy/start.sh)), since Caddy wouldn't start at all with it.
- **No `KITCHEN_API_TOKEN` on `api`**: nobody can list orders or change a status (503); the board says the kitchen isn't connected.
- **Different values on `api` and `web`**: the board loads, but says the kitchen isn't connected (the API answers 401).

To change the password, set a new hash and restart `web`. Everyone then logs in again with the new password.

## One-time setup

1. After the first image of each kind is published, make the packages public: GitHub → **SenatoreTeam** organization → **Packages** → `slicepizza-api`, `slicepizza-web` and `slicepizza-worker` → **Package settings** → **Change visibility** → Public. (The server downloads them without a password.) Only organization owners can change it.
2. On the server (in the project's compose in Dokploy):
   - Postgres: the `db` container and its volume (see [Database](#database)).
   - `api`: `ghcr.io/senatoreteam/slicepizza-api:<version>` (the newest version, e.g. `1.0.0`; the server's automatic update writes each new one here), with the database variables, `UVICORN_ROOT_PATH=/api` and `UVICORN_FORWARDED_ALLOW_IPS=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`. **No domain.**
   - `web`: `ghcr.io/senatoreteam/slicepizza-web:<version>`, the same version, on the same network as `api`, with `API_UPSTREAM` set to the API's service name and port (e.g. `api:8000`).
   - Route `slicepizza.senatore.tech` to `web` on port **8080** (`senatore.tech` and `www.senatore.tech` too, if they should keep showing the system).
   - The automatic update follows the versions of the three images (`api`, `web` and `worker`) together.
   - `rabbitmq` with a fixed hostname and its volume, and `RABBITMQ_*` on `api` (see [RabbitMQ](#rabbitmq)).
   - `worker`: `ghcr.io/senatoreteam/slicepizza-worker:<version>`, the same version, with its variables (see [Worker](#worker)). One instance only.
   - The same `INTERNAL_API_TOKEN` (`openssl rand -hex 32`) on `api` and `worker`.
   - The kitchen login: see [Kitchen](#kitchen). Until it is set, nobody can change an order's status.
   - `TELEGRAM_BOT_USERNAME` on `web` (the bot's username, without the @), so the order page shows **Follow on Telegram**. Set it once the worker has its token and `INTERNAL_API_TOKEN`; before that the button would lead to a bot that can't link the order.
3. Point the domains' DNS to the server: `A slicepizza → 179.66.139.4`, `A @ → 179.66.139.4` and `CNAME www → senatore.tech` (optionally `AAAA → 2a02:4780:95:91b7::1`). The HTTPS certificate is issued automatically once the DNS points there; if the proxy tried before that, restart the `web` container so it tries again.

### Moving from the API-only setup

Until ADR 0003 the domain pointed at the API container. To switch without downtime: publish and start `web` first (step 2), check it on the server (`curl http://<web container>:8080/api/health`), then move the domain from `api` (port 8000) to `web` (port 8080), and only then remove the domain from `api`.
