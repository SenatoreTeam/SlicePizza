"""Optional menu cache in Redis (ADR 0019).

Off unless REDIS_HOST is set. It never makes the API worse than without it:

- any Redis error (down, slow, wrong password, a bad entry, a bad REDIS_PORT)
  is logged and the request goes to Postgres as before;
- after an error the cache is marked down and requests skip it. A background
  thread (the watcher) checks Redis every ``RETRY_AFTER`` seconds and marks it
  up again. Only that thread waits for a dead Redis for long. The socket
  timeouts do not cover the DNS lookup of the host name (26 seconds in a test
  with the Redis container stopped), so every call a request makes runs in a
  helper thread and is abandoned after ``CALL_TIMEOUT``;
- entries expire by themselves (``MENU_TTL`` seconds), so a stale menu is never
  older than that. The menu only changes at startup (the seed), so before the
  cache is used, at startup and again after every error, the watcher deletes
  the cached copy: the menu is then read from Postgres once and cached again.
"""

import json
import logging
import os
import queue
import threading
import time
from concurrent.futures import Future
from typing import Any

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

logger = logging.getLogger(__name__)

MENU_KEY = "slicepizza:menu"
MENU_TTL = 60  # seconds
RETRY_AFTER = 5.0  # seconds to leave Redis alone after an error
CALL_TIMEOUT = 0.3  # seconds a request may wait for Redis, DNS lookup included
WORKERS = 4  # helper threads, so Redis calls that may run at once

_client: Any = None
_off = False  # True when REDIS_PORT is not a number: the cache stays off
_up = False  # False until the watcher has reached Redis and dropped the old copy
_down_logged = False  # the watcher has logged that Redis is down, and not seen it up since
_lock = threading.Lock()
_jobs: queue.SimpleQueue = queue.SimpleQueue()
_workers: list[threading.Thread] = []


def _get_client() -> Any:
    """The Redis client, or None when the cache is off. Starts the watcher."""
    global _client, _off
    host = os.getenv("REDIS_HOST")
    if not host or _off:
        return None
    with _lock:
        if _client is None and not _off:
            port = os.getenv("REDIS_PORT") or "6379"
            try:
                port_number = int(port)
            except ValueError:
                # The cache is optional: a bad setting turns it off, never the API.
                logger.warning("REDIS_PORT must be a number, got %r: the menu cache is off", port)
                _off = True
                return None
            _client = redis.Redis(
                host=host,
                port=port_number,
                password=os.getenv("REDIS_PASSWORD") or None,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
                # Set here, not left to redis-py, whose defaults changed in 8.0
                # (RESP3, 10 retries with backoff). RESP2 works with any Redis and
                # the cache needs nothing newer. One immediate retry replaces a
                # connection that a Redis restart closed; the watcher does the
                # slow retrying.
                protocol=2,
                retry=Retry(NoBackoff(), 1),
            )
            threading.Thread(target=_watch, args=(_client,), name="redis-watch", daemon=True).start()
    return _client


def _watch(client: Any) -> None:
    """Check Redis forever and keep ``_up`` true while it answers."""
    while True:
        _watch_once(client)
        time.sleep(RETRY_AFTER)


def _watch_once(client: Any) -> None:
    global _up, _down_logged
    try:
        if _up:
            client.ping()
        else:
            # Not in use until now (startup, or after an error): the menu may
            # have changed meanwhile (the seed), or the entry may be the bad one
            # that made a read fail. Drop it before requests use the cache.
            client.delete(MENU_KEY)
            logger.info("Redis is up: the menu is cached")
            _up = True
        _down_logged = False
    except Exception as error:  # noqa: BLE001
        # Logged once, also when Redis was never reached (wrong host or password).
        if not _down_logged:
            logger.warning("Redis is down, using the database: %s", _why(error))
            _down_logged = True
        _up = False


def _why(error: Exception) -> str:
    return str(error) or type(error).__name__  # a timeout has no message


def _failed(action: str, error: Exception) -> None:
    global _up
    _up = False  # the watcher marks it up again when Redis answers
    logger.warning("Redis %s failed, using the database: %s", action, _why(error))


def _start_workers() -> None:
    with _lock:
        while len(_workers) < WORKERS:
            # Daemons: a call stuck in a DNS lookup never holds up the API's shutdown.
            worker = threading.Thread(target=_work, name=f"redis-call-{len(_workers)}", daemon=True)
            worker.start()
            _workers.append(worker)


def _work() -> None:
    while True:
        future, function, args, kwargs = _jobs.get()
        if not future.set_running_or_notify_cancel():
            continue  # given up on while it waited for a thread: too late to be useful
        try:
            future.set_result(function(*args, **kwargs))
        except BaseException as error:  # noqa: BLE001 - handed to the caller
            future.set_exception(error)


def _call(function, *args, **kwargs):
    """Run a Redis call, giving up after CALL_TIMEOUT (raises TimeoutError).

    A call given up on while it still waits for a helper thread is cancelled,
    so it never runs late. One that already runs cannot be stopped; it finishes
    in its thread.
    """
    if len(_workers) < WORKERS:
        _start_workers()
    future: Future = Future()
    _jobs.put((future, function, args, kwargs))
    try:
        return future.result(timeout=CALL_TIMEOUT)
    except TimeoutError:
        future.cancel()
        raise


def _usable() -> Any:
    client = _get_client()
    return client if client is not None and _up else None


def get_menu() -> list[dict] | None:
    """The cached menu, or None (cache off, empty or failing)."""
    client = _usable()
    if client is None:
        return None
    try:
        raw = _call(client.get, MENU_KEY)
        menu = json.loads(raw) if raw else None
        if menu is not None and not isinstance(menu, list):
            raise ValueError(f"{MENU_KEY} holds a {type(menu).__name__}, not a menu")
    except Exception as error:  # noqa: BLE001 - the cache must never break a request
        _failed("read", error)  # a bad entry is dropped by the watcher
        return None
    return menu


def set_menu(menu: list[dict]) -> None:
    client = _usable()
    if client is None:
        return
    try:
        _call(client.set, MENU_KEY, json.dumps(menu), ex=MENU_TTL)
    except Exception as error:  # noqa: BLE001
        _failed("write", error)


def clear_menu() -> None:
    """Drop the cached menu, which may have changed (the API calls this after the seed).

    At startup the cache is not up yet, so this only starts the client: the
    watcher drops the old copy before requests use the cache.
    """
    client = _usable()
    if client is None:
        return
    try:
        _call(client.delete, MENU_KEY)
    except Exception as error:  # noqa: BLE001
        _failed("delete", error)
