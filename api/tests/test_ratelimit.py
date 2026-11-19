"""The order rate limit (ADR 0021)."""

import pytest

from app import ratelimit

ORDER = {
    "customer": {"name": "Ana", "phone": "11999990000", "address": "Rua A, 1"},
    "items": [{"pizza_id": 1, "quantity": 1}],
}


@pytest.fixture(autouse=True)
def clean_limiter():
    ratelimit.orders_limiter.reset()
    yield
    ratelimit.orders_limiter.reset()


def test_orders_beyond_the_limit_get_429_with_retry_after(client, monkeypatch):
    monkeypatch.setenv("ORDER_RATE_LIMIT", "3")
    for _ in range(3):
        assert client.post("/orders", json=ORDER).status_code == 201
    blocked = client.post("/orders", json=ORDER)
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1


def test_the_limit_can_be_turned_off(client, monkeypatch):
    monkeypatch.setenv("ORDER_RATE_LIMIT", "0")
    for _ in range(5):
        assert client.post("/orders", json=ORDER).status_code == 201


def test_reading_the_menu_is_never_limited(client, monkeypatch):
    monkeypatch.setenv("ORDER_RATE_LIMIT", "1")
    for _ in range(10):
        assert client.get("/menu").status_code == 200


def test_the_window_slides():
    limiter = ratelimit.SlidingWindowLimiter()
    assert limiter.check("a", 2, 60, now=0) == 0
    assert limiter.check("a", 2, 60, now=1) == 0
    assert limiter.check("a", 2, 60, now=2) == pytest.approx(58)  # wait for the first to expire
    assert limiter.check("a", 2, 60, now=61) == 0  # the first hit left the window


def test_clients_are_counted_apart():
    limiter = ratelimit.SlidingWindowLimiter()
    assert limiter.check("a", 1, 60, now=0) == 0
    assert limiter.check("b", 1, 60, now=0) == 0
    assert limiter.check("a", 1, 60, now=1) > 0


def test_old_clients_are_forgotten(monkeypatch):
    monkeypatch.setattr(ratelimit, "MAX_CLIENTS", 3)
    limiter = ratelimit.SlidingWindowLimiter()
    for i in range(10):
        limiter.check(f"c{i}", 1, 60, now=0)
    limiter.check("late", 1, 60, now=1000)  # triggers the purge of expired clients
    assert len(limiter._hits) <= 3
