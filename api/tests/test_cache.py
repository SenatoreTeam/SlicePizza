"""The Redis menu cache (ADR 0019): fast when it works, invisible when it fails."""

import threading
import time
from concurrent.futures import Future

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

    def ping(self):
        self._check()
        return True


@pytest.fixture
def fake(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(cache, "_get_client", lambda: fake)
    monkeypatch.setattr(cache, "_up", True)
    monkeypatch.setattr(cache, "_down_logged", False)
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
    def slow_get(key):
        time.sleep(2)

    monkeypatch.setattr(fake, "get", slow_get)
    monkeypatch.setattr(cache, "CALL_TIMEOUT", 0.1)
    started = time.monotonic()
    assert client.get("/menu").status_code == 200
    assert time.monotonic() - started < 1.0
    assert cache._up is False


@pytest.mark.parametrize(
    "entry",
    [
        b"not json",
        b"\xff\xfe",
        b'{"not": "a list"}',
        b"42",
        # Lists, but not of pizzas in the menu's shape (another version of the API wrote them).
        b"[1, 2]",
        b'[{"id": 1}]',
        b'[{"id": 1, "name": "X", "description": "", "price_cents": "abc", "available": true}]',
    ],
)
def test_a_bad_entry_in_redis_falls_back_to_the_database(client, fake, entry):
    fake.data[cache.MENU_KEY] = entry
    response = client.get("/menu")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert cache._up is False  # and the watcher drops the entry before using the cache again
    cache._watch_once(fake)
    assert cache.MENU_KEY not in fake.data
    assert cache._up is True


def test_the_watcher_drops_the_old_menu_before_the_cache_is_used(fake, monkeypatch):
    # At startup (or after an outage) Redis may still hold the menu from before the seed.
    monkeypatch.setattr(cache, "_up", False)
    fake.data[cache.MENU_KEY] = b'[{"id": 1, "name": "Old"}]'
    cache._watch_once(fake)
    assert cache.MENU_KEY not in fake.data
    assert cache._up is True


def test_while_redis_is_up_the_watcher_only_pings(fake):
    fake.data[cache.MENU_KEY] = b"[]"
    cache._watch_once(fake)
    assert fake.data[cache.MENU_KEY] == b"[]"
    assert cache._up is True


def test_a_redis_never_reached_is_logged_once(fake, monkeypatch, caplog):
    # A wrong host or password: Redis is never up, which must still show in the logs.
    monkeypatch.setattr(cache, "_up", False)
    fake.broken = True
    for _ in range(3):
        cache._watch_once(fake)
    warnings = [r for r in caplog.records if r.name == "app.cache" and r.levelname == "WARNING"]
    assert len(warnings) == 1
    assert "Redis is down" in warnings[0].getMessage()
    assert cache._up is False
    # Once it is reached, the next outage is logged again.
    fake.broken = False
    cache._watch_once(fake)
    fake.broken = True
    cache._watch_once(fake)
    warnings = [r for r in caplog.records if r.name == "app.cache" and r.levelname == "WARNING"]
    assert len(warnings) == 2


def test_a_timeout_says_so_in_the_log(client, fake, monkeypatch, caplog):
    monkeypatch.setattr(fake, "get", lambda key: time.sleep(1))
    monkeypatch.setattr(cache, "CALL_TIMEOUT", 0.05)
    client.get("/menu")
    assert "Redis read failed, using the database: TimeoutError" in caplog.text


def test_a_call_given_up_on_never_runs_later(monkeypatch):
    monkeypatch.setattr(cache, "CALL_TIMEOUT", 0.05)
    release = threading.Event()
    started = threading.Semaphore(0)

    def stuck():
        started.release()
        release.wait()

    cache._start_workers()
    try:
        for _ in range(cache.WORKERS):
            cache._jobs.put((Future(), stuck, (), {}))
        for _ in range(cache.WORKERS):  # every helper thread is now stuck, like Redis hanging
            assert started.acquire(timeout=5)
        late = []
        with pytest.raises(TimeoutError):
            cache._call(late.append, "written long after the request")
    finally:
        release.set()
    time.sleep(0.2)
    assert late == []


def test_the_helper_threads_never_hold_up_shutdown(fake, client):
    client.get("/menu")
    threads = [t for t in threading.enumerate() if t.name.startswith("redis-call")]
    assert len(threads) == cache.WORKERS
    assert all(t.daemon for t in threads)


def test_a_bad_redis_port_turns_only_the_cache_off(monkeypatch, caplog):
    monkeypatch.setattr(cache, "_client", None)
    monkeypatch.setattr(cache, "_off", False)
    monkeypatch.setenv("REDIS_HOST", "redis")
    monkeypatch.setenv("REDIS_PORT", "redis:6379")
    assert cache._get_client() is None
    assert cache._get_client() is None
    assert caplog.text.count("REDIS_PORT must be a number") == 1
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as started:  # the API starts and the menu works
        assert started.get("/menu").status_code == 200


def test_the_client_does_not_rely_on_redis_py_defaults(monkeypatch):
    # redis-py 8 changed them (RESP3, 10 retries with backoff): the cache sets its own.
    monkeypatch.setattr(cache, "_client", None)
    monkeypatch.setattr(cache, "_off", False)
    monkeypatch.setattr(cache, "_watch", lambda client: None)  # no thread pinging a fake host
    monkeypatch.setenv("REDIS_HOST", "redis.invalid")
    monkeypatch.delenv("REDIS_PORT", raising=False)
    settings = cache._get_client().connection_pool.connection_kwargs
    assert settings["protocol"] == 2
    assert settings["retry"].get_retries() == 1
    assert settings["socket_timeout"] == 0.2


def test_a_bad_entry_is_logged_on_one_line(client, fake, caplog):
    fake.data[cache.MENU_KEY] = b'[{"id": 1}]'
    client.get("/menu")
    lines = [r.getMessage() for r in caplog.records if r.name == "app.cache"]
    assert len(lines) == 1
    assert lines[0].startswith("Redis read failed, using the database: ")
    assert "\n" not in lines[0]
