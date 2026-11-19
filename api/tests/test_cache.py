"""The Redis menu cache (ADR 0019): fast when it works, invisible when it fails."""

import pytest

from app import cache


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.calls = 0
        self.broken = False

    def _check(self):
        self.calls += 1
        if self.broken:
            raise ConnectionError("redis is down")

    def get(self, key):
        self._check()
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self._check()
        self.data[key] = value

    def delete(self, key):
        self._check()
        self.data.pop(key, None)


@pytest.fixture
def fake(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(cache, "_get_client", lambda: fake)
    monkeypatch.setattr(cache, "_up", True)
    return fake


def test_without_redis_the_menu_still_works(client, monkeypatch):
    monkeypatch.setattr(cache, "_get_client", lambda: None)
    assert client.get("/menu").status_code == 200


def test_second_request_comes_from_the_cache(client, db, fake):
    first = client.get("/menu").json()
    assert cache.MENU_KEY in fake.data
    # Change the database behind the cache's back: the cached copy is served.
    from app.models import Pizza

    db.get(Pizza, 1).name = "Changed"
    db.commit()
    assert client.get("/menu").json() == first


def test_cached_menu_is_the_same_as_the_database_one(client, fake):
    from_db = client.get("/menu").json()
    from_cache = client.get("/menu").json()
    assert from_db == from_cache
    assert {"id", "name", "description", "price_cents", "available"} <= set(from_db[0])


def test_a_broken_redis_does_not_break_the_menu(client, fake):
    fake.broken = True
    response = client.get("/menu")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_after_an_error_redis_is_left_alone_until_the_watcher_sees_it_up(client, fake):
    fake.broken = True
    client.get("/menu")
    calls = fake.calls
    client.get("/menu")
    client.get("/menu")
    assert fake.calls == calls  # marked down: no request waits for Redis again
    assert cache._up is False


def test_a_cache_that_is_not_up_yet_is_not_used(client, fake, monkeypatch):
    monkeypatch.setattr(cache, "_up", False)
    client.get("/menu")
    assert fake.calls == 0


def test_a_redis_that_hangs_costs_a_request_no_more_than_the_timeout(client, fake, monkeypatch):
    import time

    def slow_get(key):
        time.sleep(2)

    monkeypatch.setattr(fake, "get", slow_get)
    monkeypatch.setattr(cache, "CALL_TIMEOUT", 0.1)
    started = time.monotonic()
    assert client.get("/menu").status_code == 200
    assert time.monotonic() - started < 1.0
    assert cache._up is False
