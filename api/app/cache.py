"""Optional menu cache in Redis (ADR 0019).

Off unless REDIS_HOST is set. It never makes the API worse than without it:

- any Redis error (down, slow, wrong password) is logged and the request goes
  to Postgres as before;
- after an error the cache is marked down and requests skip it. A background
  thread pings Redis every ``RETRY_AFTER`` seconds and marks it up again. Only
  that thread waits for a dead Redis for long. The socket timeouts do not
  cover the DNS lookup of the host name (26 seconds in a test with the Redis
  container stopped), so every call a request makes runs in a helper thread
  and is abandoned after ``CALL_TIMEOUT``;
- entries expire by themselves (``MENU_TTL`` seconds), so a stale menu is never
  older than that. The menu only changes at startup (the seed), and the API
  clears the key then.
"""

import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import redis

logger = logging.getLogger(__name__)

MENU_KEY = "slicepizza:menu"
MENU_TTL = 60  # seconds
RETRY_AFTER = 5.0  # seconds to leave Redis alone after an error

_client: Any = None
_up = False  # False until the background thread has reached Redis
_lock = threading.Lock()
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="redis-call")
CALL_TIMEOUT = 0.3  # seconds a request may wait for Redis, DNS lookup included


def _get_client() -> Any:
    """The Redis client, or None when the cache is off. Starts the watcher."""
    global _client
    host = os.getenv("REDIS_HOST")
    if not host:
        return None
    with _lock:
        if _client is None:
            _client = redis.Redis(
                host=host,
                port=int(os.getenv("REDIS_PORT") or "6379"),
                password=os.getenv("REDIS_PASSWORD") or None,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
            )
            threading.Thread(target=_watch, args=(_client,), name="redis-watch", daemon=True).start()
    return _client


def _watch(client: Any) -> None:
    """Ping Redis forever and keep ``_up`` true while it answers."""
    global _up
    while True:
        try:
            client.ping()
            if not _up:
                logger.info("Redis is up: the menu is cached")
            _up = True
        except Exception as error:  # noqa: BLE001
            if _up:
                logger.warning("Redis is down, using the database: %s", error)
            _up = False
        time.sleep(RETRY_AFTER)


def _failed(action: str, error: Exception) -> None:
    global _up
    _up = False  # the watcher marks it up again when Redis answers
    logger.warning("Redis %s failed, using the database: %s", action, error)


def _call(function, *args, **kwargs):
    """Run a Redis call, giving up after CALL_TIMEOUT (raises TimeoutError)."""
    return _pool.submit(function, *args, **kwargs).result(timeout=CALL_TIMEOUT)


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
    except Exception as error:  # noqa: BLE001 - the cache must never break a request
        _failed("read", error)
        return None
    return json.loads(raw) if raw else None


def set_menu(menu: list[dict]) -> None:
    client = _usable()
    if client is None:
        return
    try:
        _call(client.set, MENU_KEY, json.dumps(menu), ex=MENU_TTL)
    except Exception as error:  # noqa: BLE001
        _failed("write", error)


def clear_menu() -> None:
    client = _usable()
    if client is None:
        return
    try:
        _call(client.delete, MENU_KEY)
    except Exception as error:  # noqa: BLE001
        _failed("delete", error)
