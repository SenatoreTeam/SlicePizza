# Product tour

Screenshots of the system running locally with `docker compose up`. All names, phones and addresses are fictional demo data.

## The menu site

Customers pick pizzas from the menu served at the site root. The page talks to the API through `/api` (same domain, [ADR 0003](/adr/0003-one-domain-caddy-in-front)).

![The menu with prices and quantity pickers](@site/static/img/screenshots/menu.png)

On a phone the layout collapses into a single column, with the total and the order button pinned to the bottom:

![The menu on a phone](@site/static/img/screenshots/menu-mobile.png)

## Placing an order

After choosing pizzas, the customer fills in name, phone and delivery address. The order is validated by the API, so prices always come from the database and never from the browser.

![The delivery form with the cart total](@site/static/img/screenshots/menu-order-form.png)

## Following the order

Each order gets its own page showing the four stages: received, being prepared, on the way and delivered. With Telegram configured, a "Follow on Telegram" button also appears here.

![The order status page](@site/static/img/screenshots/order-status.png)

## The kitchen board

The pizzeria sees orders at `/kitchen/`, behind a login ([ADR 0007](/adr/0007-kitchen-login)). Orders move from **New** to **In the oven** to **On the way** with a single button, and can be cancelled while they are new.

![The kitchen board with orders in three columns](@site/static/img/screenshots/kitchen-board.png)

## The API

FastAPI publishes interactive documentation at `/api/docs` (and at `/docs` when you run the API on its own).

![Swagger UI listing the API routes](@site/static/img/screenshots/api-docs.png)
