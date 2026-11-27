# Frontend

Plain HTML, CSS and JavaScript, with no build step and no framework (the project's focus is DevOps, not front-end).

| Page | Folder | Address | For whom | Phase |
|---|---|---|---|---|
| Menu website | [`menu/`](menu/) | `https://slicepizza.senatore.tech/` | Customers pick pizzas, place an order and follow its status | 2 |
| Kitchen board | [`kitchen/`](kitchen/) | `https://slicepizza.senatore.tech/kitchen/` (with a password) | The kitchen sees the open orders and moves them along | 3 |

## Menu website

```
menu/
├── index.html   # the page: menu, delivery form, order tracking
├── app.js       # talks to the API and renders the page
├── styles.css
├── config.js    # the API address and the Telegram bot; Caddy fills in the bot
└── favicon.svg
```

What it does:

1. Loads the menu from `GET /menu`.
2. The customer picks quantities and fills in name, phone and address.
3. **Place order** sends `POST /orders`, then opens `#/order/<id>`.
4. The order page calls `GET /orders/<id>` every 10 seconds until the order is delivered or cancelled, and pauses while the tab is in the background. After an error it retries further apart each time (up to once a minute). The last order is remembered in the browser, so the customer can find it again from the menu.
5. While the order is still on its way, the page shows **Follow on Telegram** (see below).

If an order fails because a pizza left the menu (404) or sold out (409), the page reloads the menu and takes that pizza out of the basket.

The page is a single file with two views selected by the URL hash, so any static host can serve it: no server-side routing needed.

### Running it locally

With the rest of the stack, from the repository root:

```bash
docker compose up --build
```

Open <http://localhost:8080>. The `web` service is the production image ([`infra/caddy/`](../infra/caddy/)): Caddy serves the copy of `frontend/menu/` inside the image and forwards `/api/*` to the API, so a change to the site needs `--build`.

To edit the site and just reload the page, add the file that mounts your working copy over the image's:

```bash
docker compose -f docker-compose.yml -f docker-compose.site-dev.yml up --build
```

Caddy runs as uid 10001, so the files must be readable by others: with a umask of 077, run `chmod -R o+rX frontend/menu` first.

Without Docker, run the API with Uvicorn on port 8000 (see [api/README.md](../api/README.md#running)) and Caddy with the same Caddyfile, pointing it at your folders:

```bash
SITE_ROOT=frontend/menu API_HOST=localhost API_PORT=8000 caddy run --config infra/caddy/Caddyfile
```

### Talking to the API

The site calls the API at **`/api`, on its own domain** (`config.js`). In production that is `https://slicepizza.senatore.tech/api/...`; locally, `http://localhost:8080/api/...`. Same origin, so the browser needs no CORS ([ADR 0003](../docs/adr/0003-one-domain-caddy-in-front.md)).

Every call goes through the `api()` helper in `app.js`. It always sends **`Content-Type: application/json`** with a body, which the API requires ([issue #25](https://github.com/SenatoreTeam/SlicePizza/issues/25)), and turns the API's errors into messages for the customer.

When something fails, the page says which side it was:

- **"The pizzeria's system is offline for a moment"**: an answer came, but it was 502, 503 or 504. Either the API is down or `web` cannot reach it (Caddy answers 502: check `API_UPSTREAM`), or the API is up without its database (503). Open `/api/health` in the same browser to tell which.
- **"Couldn't reach the pizzeria"**: no answer at all. The connection is down, or the browser blocked the call: open the browser's console, where a blocked call shows as a Content-Security-Policy or CORS error.

### Follow on Telegram

The order page can offer a **Follow on Telegram** button: it opens `https://t.me/<bot>?start=<order id>`, and when the customer presses *Start*, the notification worker links that chat to the order and sends its updates there ([ADR 0006](../docs/adr/0006-customer-telegram-opt-in.md)).

The bot's username comes from the `TELEGRAM_BOT_USERNAME` setting on the `web` container. Caddy serves `config.js` as a template and fills it in (escaped for a JavaScript string), so the same image works with any bot, or none:

```js
telegramBot: '{{env "TELEGRAM_BOT_USERNAME" | js}}',
```

No setting, or anything that isn't a Telegram username, means no button. That is also what you get when you open the files without Caddy: the raw template is not a username. The button is hidden once the order is delivered or cancelled, since no more updates will come.

### Pointing it at another API

`config.js` holds the API address and is the only file that knows it:

```js
window.SLICEPIZZA_CONFIG = {
  apiUrl: "/api",
};
```

To use an API on another origin (e.g. `"http://localhost:8000"`), three things change:

1. Put its full address in `config.js`.
2. Allow the page to call it: set `EXTRA_CONNECT_SRC` to that origin (e.g. `http://localhost:8000`) on the `web` container. Caddy adds it to the page's Content-Security-Policy (`connect-src`), which otherwise only allows the site's own origin.
3. Add this site's origin to the API's `CORS_ORIGINS` (see [api/README.md](../api/README.md#calling-the-api-from-a-browser-cors)).

## Kitchen board

```
kitchen/
├── index.html   # three rails: New, In the oven, On the way
├── kitchen.js   # loads the open orders every 5 seconds, moves them along
└── kitchen.css
```

Served at **`/kitchen/`** ([ADR 0024](../docs/adr/0024-kitchen-login-in-the-api.md)). The page itself is public and holds no data: it asks for the kitchen's password, logs in with `POST /kitchen/api/session`, and the API answers with a session cookie (`HttpOnly`, 12 hours) that the page cannot read. Its calls go to `/kitchen/api/...`, which Caddy forwards to the API. **Log out** ends the session; 5 wrong passwords lock the address for 15 minutes.

What it does:

1. Shows each open order as a ticket on its rail, oldest first. A ticket shows how long the order has waited, what to make, and who it's for. Past 30 minutes, the time turns red.
2. One button per ticket moves the order to the next status. New orders can also be cancelled, after a confirmation.
3. Refreshes every 5 seconds and right after every change. New tickets flash once, and screen readers announce them. Tickets are only redrawn when something on them changed, so a tap is never lost to a refresh.
4. If another screen moved an order first, it says so and shows where the order is now. If the API can't be reached, it keeps showing the last orders it loaded, says since when, and retries further apart each time (up to once a minute).

To try it locally, set `KITCHEN_API_TOKEN` and `KITCHEN_PASSWORD_HASH` in `.env` (see `.env.example`), run `docker compose up -d`, and open <http://localhost:8080/kitchen/>. The login asks only for the password. The page is served from the `web` image; `docker-compose.site-dev.yml` mounts `frontend/kitchen/` too, for live edits.

## Fonts

The fonts (Instrument Sans and Young Serif) are served from `menu/fonts/`, not from Google Fonts: a visitor's IP address must not go to a third party just for opening the page (LGPD, [`.lgpd/`](../.lgpd/data-map.en.md)). Both are under the SIL Open Font License (the licenses are next to the files). The Content-Security-Policy in `infra/caddy/Caddyfile` allows only this site's own fonts and styles, so adding a font from a CDN will be blocked on purpose: put the file in `menu/fonts/` and add it to `fonts/fonts.css` instead.
