# 0015: Alerts to Telegram through Grafana's own alerting

- **Status:** Superseded by [0016](0016-server-monitoring.md): the server's own monitoring replaces this stack
- **Date:** 2026-11-17
- **Phase:** 5

## Context

Dashboards ([ADR 0013](0013-prometheus-and-grafana.md)) and logs ([ADR 0014](0014-loki-and-alloy.md)) only help when someone looks. The team should be told when the system is down or orders stop reaching the kitchen, in the chat they already read.

## Options considered

1. **Grafana alerting, provisioned from Git, contact point Telegram.** Grafana already has both datasources (Prometheus and Loki), so one rule can use numbers or logs. No new container.
2. **Prometheus Alertmanager + a Telegram bridge.** Standard, but two new containers and rules that cannot look at logs.
3. **The Telegram worker sends its own alerts.** It would be silent exactly when the worker or RabbitMQ is the thing that broke.
4. **A hosted uptime tool only.** Planned anyway as an *outside* check (5.6), since an alert from inside the server cannot say "the server is gone". It does not know about the outbox or queues.

## Decision

Option 1, in [`infra/monitoring/grafana/provisioning/alerting/`](https://github.com/SenatoreTeam/SlicePizza/tree/42d4bf78dcaba0cb6145556758ec11b9c9373002/infra/monitoring/grafana/provisioning/alerting) (removed by ADR 0016; the link shows the last version):

- **Contact point** `telegram-ops`: bot token and chat id come from `ALERT_TELEGRAM_BOT_TOKEN` and `ALERT_TELEGRAM_CHAT_ID` on the Grafana container, never from the repo. The **same bot** as the worker can be used (same token, set in both places; rotating it means updating both); send to a **separate ops chat**, not the pizzeria's, so the kitchen does not get alerts. Tradeoff: if Telegram rejects that bot, orders and alerts fail together. Grafana refuses an empty token, so the compose defaults are placeholders; with them alerts fail to send (logged) and nothing else breaks.
- **Rules** (checked every 30 seconds, each must hold for a while so a blip stays quiet): API down (`up{job="api"}`, 30 s, also fires when there is no data), more than 5% of requests are 5xx (5 min), oldest outbox event older than 5 minutes (2 min), a RabbitMQ queue above 50 waiting messages (10 min), more than 20 error lines from the API in 5 minutes (from Loki).
- **Routing**: one policy, grouped by alert name, repeat every 4 hours while still firing; "resolved" messages are on; first message 10 s after an alert fires.

## Consequences

- Verified locally: Grafana loads the contact point and all five rules without errors. A real Telegram delivery was **not** tested (needs the bot added to the ops chat).
- **Down-on-purpose test (local, 2026-11-18):** stopping the API made "API is down" fire after 56 seconds and route to `telegram-ops` (the first try, with a 1-minute check and a 2-minute hold, took 181 seconds, which is why the numbers above are tighter). The message itself was not delivered (no real bot token).
- Alerts live in the same Grafana: if Grafana or the server is down, no message. The external check (5.6) covers that.
- The thresholds are a first guess for a small system; tune them after a few weeks of real numbers.
- Disk usage is not alerted yet: it needs a node exporter, a later decision.
- Server step: set the two variables on `grafana` (see `docs/DEPLOY.md`, "Monitoring").
