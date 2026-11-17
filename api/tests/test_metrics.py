"""The Prometheus metrics (ADR 0012)."""

from datetime import UTC, datetime, timedelta

import pytest

from app import metrics
from app.database import SessionLocal
from app.models import OrderEvent

ORDER_PAYLOAD = {
    "customer": {"name": "Zé", "phone": "+55 11 99999-0000", "address": "Rua das Pizzas, 42"},
    "items": [{"pizza_id": 1, "quantity": 2}],
}


def create_order(client):
    return client.post("/orders", json=ORDER_PAYLOAD)


@pytest.fixture(autouse=True)
def fresh_metrics():
    metrics.reset()


def scrape(client) -> str:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    return response.text


def test_metrics_are_not_in_the_api_docs(client):
    assert "/metrics" not in client.get("/openapi.json").json()["paths"]


def test_requests_are_counted_by_route_template(client):
    client.get("/menu")
    client.get("/menu")
    text = scrape(client)
    assert 'slicepizza_http_requests_total{method="GET",route="/menu",status="200"} 2' in text
    assert 'slicepizza_http_request_duration_seconds_count{method="GET",route="/menu"} 2' in text
    assert 'slicepizza_http_request_duration_seconds_bucket{method="GET",route="/menu",le="+Inf"} 2' in text


def test_the_route_label_is_the_template_not_the_url(client):
    client.get("/orders/00000000-0000-0000-0000-000000000001")
    text = scrape(client)
    assert 'route="/orders/{order_id}"' in text
    assert "0000-0000-0000-000000000001" not in text


def test_unknown_urls_share_one_label(client):
    client.get("/nope-1")
    client.get("/nope-2")
    text = scrape(client)
    assert 'route="unmatched",status="404"} 2' in text
    assert "nope" not in text


def test_the_scrape_itself_is_not_counted(client):
    scrape(client)
    assert 'route="/metrics"' not in scrape(client)


def test_created_orders_are_counted(client):
    assert create_order(client).status_code == 201
    assert "slicepizza_orders_created_total 1" in scrape(client)


def test_the_outbox_backlog_is_reported(client):
    assert "slicepizza_outbox_pending_events 0" in scrape(client)
    assert "slicepizza_outbox_oldest_pending_age_seconds 0.0" in scrape(client)

    create_order(client)  # no RabbitMQ in the tests: its event waits
    with SessionLocal() as db:
        event = db.query(OrderEvent).one()
        event.created_at = datetime.now(UTC) - timedelta(seconds=120)
        db.commit()
    text = scrape(client)
    assert "slicepizza_outbox_pending_events 1" in text
    line = next(row for row in text.splitlines() if row.startswith("slicepizza_outbox_oldest_pending_age_seconds "))
    age = float(line.split()[1])
    assert 119 <= age < 150


def test_build_info_says_the_version(client, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "1.4.2")
    monkeypatch.setenv("GIT_COMMIT", "abc")
    assert 'slicepizza_build_info{release="1.4.2",commit="abc"} 1' in scrape(client)
