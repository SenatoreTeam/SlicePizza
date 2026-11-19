"""Per-client rate limit for placing orders (Phase 8, ADR 0021).

Every order reaches the kitchen and the pizzeria's Telegram, so a script that
posts orders in a loop costs real attention, not only CPU. Each client address
may place ``ORDER_RATE_LIMIT`` orders per ``ORDER_RATE_WINDOW`` seconds
(default 30 per 60); past that the API answers 429 with ``Retry-After``.
``ORDER_RATE_LIMIT=0`` turns it off.

The counters live in this process: with several API copies each counts on its
own, so the real limit is at most copies x the setting. That is enough to stop
abuse, and keeps the API free of another dependency for it.

The client address is the one Uvicorn gives after reading X-Forwarded-For from
Caddy. If the proxies in front were misconfigured so that every customer looked
like one address, this would limit everybody together: docs/DEPLOY.md says how
to check, and a 429 is logged with the address it was for.
"""

import logging
import os
import threading
import time
from collections import deque

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 30
DEFAULT_WINDOW = 60.0
MAX_CLIENTS = 10_000  # bound on remembered addresses


def _number(name: str, default: float) -> float:
    try:
        return float(os.getenv(name) or default)
    except ValueError:
        return default


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window: float, now: float | None = None) -> float:
        """Record a hit. Returns 0 if allowed, else the seconds to wait."""
        now = time.monotonic() if now is None else now
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - window:
                hits.popleft()
            if len(hits) >= limit:
                return max(hits[0] + window - now, 0.001)
            hits.append(now)
            if len(self._hits) > MAX_CLIENTS:
                self._purge(now, window)
            return 0.0

    def _purge(self, now: float, window: float) -> None:
        for key in [k for k, h in self._hits.items() if not h or h[-1] <= now - window]:
            del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


orders_limiter = SlidingWindowLimiter()


def limit_orders(request: Request) -> None:
    """FastAPI dependency for POST /orders."""
    limit = int(_number("ORDER_RATE_LIMIT", DEFAULT_LIMIT))
    if limit <= 0:
        return
    window = _number("ORDER_RATE_WINDOW", DEFAULT_WINDOW)
    client = request.client.host if request.client else "unknown"
    wait = orders_limiter.check(client, limit, window)
    if wait:
        logger.warning("Order rate limit reached for %s (%d per %.0fs)", client, limit, window)
        raise HTTPException(
            status_code=429,
            detail="Too many orders from this address. Try again in a moment.",
            headers={"Retry-After": str(int(wait) + 1)},
        )
