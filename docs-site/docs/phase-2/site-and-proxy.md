# Phase 2 — The site and the proxy

This page explains **how the pieces fit together**. For the files, settings and
commands, see the [frontend README](../../../frontend/README.md) and
[DEPLOY.md](../../../docs/DEPLOY.md).

## One domain, two kinds of requests

```
https://slicepizza.senatore.tech
        │   (the server's proxy handles HTTPS)
        ▼
   web container: Caddy, port 8080
        ├── /api/*  ──►  api container (the Orders API), with "/api" removed
        └── anything else  ──►  the menu website's files
```

The roadmap suggested a CDN for the site and separate `api` and `admin`
subdomains. SlicePizza runs on a shared server that already has a domain, Docker
and an HTTPS proxy, so it uses a simpler layout: **one domain, with Caddy
deciding by path**. The reasons and trade-offs are in
[ADR 0003](../../../docs/adr/0003-one-domain-caddy-in-front.md).

A useful side effect: the site and the API share an origin, so the browser never
needs CORS to call the API, and CORS stays switched off.

## The menu website

The site has no framework and no build step: `index.html`, `app.js`, `styles.css`
and a small `config.js`. A customer's journey:

1. The menu loads from `GET /api/menu`.
2. The customer picks pizzas and fills in name, phone and address.
3. `POST /api/orders` creates the order, and the page moves to the order's status
   page.
4. The status page asks for the order every 10 seconds until it is delivered or
   cancelled, and pauses while the tab is in the background.

| Placing the order | Following it |
| --- | --- |
| ![The delivery form with the cart total](@site/static/img/screenshots/menu-order-form.png) | ![The order status page with its four stages](@site/static/img/screenshots/order-status.png) |

Text from the API is only ever inserted into the page as **text**, never as HTML,
and a Content-Security-Policy set by Caddy only lets the page load its own
scripts.

## What the API needs to know

Two small settings make the API behave correctly behind the proxy:

- `UVICORN_ROOT_PATH=/api`, so the API's own `/docs` page finds its schema under
  `/api`.
- `UVICORN_FORWARDED_ALLOW_IPS`, so the API trusts the `X-Forwarded-*` headers
  only when they come from the private network the proxy lives in.

## From merge to production

```
merge to main ──► GitHub Actions builds the images ──► GitHub container registry
                                                         │
                          the server checks for new images every 5 minutes
```

Nothing is copied to the server by hand. The steps for the first setup and for
moving from the earlier API-only layout are in
[DEPLOY.md](../../../docs/DEPLOY.md).
