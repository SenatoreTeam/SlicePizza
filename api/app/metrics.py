"""Prometheus metrics for the API (Phase 5, ADR 0012).

Written by hand in Prometheus' text format instead of with a library: the API
runs one Uvicorn process, so plain in-memory counters are enough, and the
image gets no new dependency. If the API ever runs several workers, switch to
prometheus_client's multiprocess mode.

Labels are kept few and bounded, so the numbers stay small: the route is the
*template* ("/orders/{order_id}"), never the real URL, and a request that
matches no route is counted as "unmatched".
"""

import os
import threading
import time
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import OrderEvent

# Seconds. Orders are small database calls, so the buckets are fine at the low end.
BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
METRICS_PATH = "/metrics"

_lock = threading.Lock()
_requests: dict[tuple[str, str, str], int] = {}
# (method, route) -> [bucket counts..., +Inf count, sum]
_durations: dict[tuple[str, str], list[float]] = {}
_orders_created = 0


def observe_request(method: str, route: str, status_code: int, seconds: float) -> None:
    with _lock:
        key = (method, route, str(status_code))
        _requests[key] = _requests.get(key, 0) + 1
        row = _durations.setdefault((method, route), [0] * (len(BUCKETS) + 1) + [0.0])
        for i, bound in enumerate(BUCKETS):
            if seconds <= bound:
                row[i] += 1
        row[len(BUCKETS)] += 1
        row[-1] += seconds


def order_created() -> None:
    global _orders_created
    with _lock:
        _orders_created += 1


def reset() -> None:
    """Forget everything (for the tests)."""
    global _orders_created
    with _lock:
        _requests.clear()
        _durations.clear()
        _orders_created = 0


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _labels(**labels: str) -> str:
    return "{" + ",".join(f'{k}="{_escape(v)}"' for k, v in labels.items()) + "}"


def render(db: Session) -> str:
    """The metrics in Prometheus' text format. Reads the outbox from the database."""
    pending, oldest = db.execute(
        select(func.count(), func.min(OrderEvent.created_at)).where(OrderEvent.published_at.is_(None))
    ).one()
    age = 0.0
    if oldest is not None:
        if oldest.tzinfo is None:  # SQLite returns naive datetimes
            oldest = oldest.replace(tzinfo=UTC)
        age = max(0.0, (datetime.now(UTC) - oldest).total_seconds())

    lines = [
        "# HELP slicepizza_build_info The version this API runs (always 1).",
        "# TYPE slicepizza_build_info gauge",
        "slicepizza_build_info"
        + _labels(release=os.getenv("APP_VERSION") or "unknown", commit=os.getenv("GIT_COMMIT") or "unknown")
        + " 1",
        "# HELP slicepizza_orders_created_total Orders created since the API started.",
        "# TYPE slicepizza_orders_created_total counter",
    ]
    with _lock:
        lines.append(f"slicepizza_orders_created_total {_orders_created}")
        lines += [
            "# HELP slicepizza_http_requests_total HTTP requests by method, route and status.",
            "# TYPE slicepizza_http_requests_total counter",
        ]
        for (method, route, code), count in sorted(_requests.items()):
            lines.append(
                "slicepizza_http_requests_total" + _labels(method=method, route=route, status=code) + f" {count}"
            )
        lines += [
            "# HELP slicepizza_http_request_duration_seconds Time to answer a request.",
            "# TYPE slicepizza_http_request_duration_seconds histogram",
        ]
        for (method, route), row in sorted(_durations.items()):
            base = {"method": method, "route": route}
            for i, bound in enumerate(BUCKETS):
                lines.append(
                    "slicepizza_http_request_duration_seconds_bucket" + _labels(**base, le=str(bound)) + f" {row[i]}"
                )
            lines.append(
                "slicepizza_http_request_duration_seconds_bucket" + _labels(**base, le="+Inf") + f" {row[len(BUCKETS)]}"
            )
            lines.append("slicepizza_http_request_duration_seconds_sum" + _labels(**base) + f" {row[-1]}")
            lines.append("slicepizza_http_request_duration_seconds_count" + _labels(**base) + f" {row[len(BUCKETS)]}")
    lines += [
        "# HELP slicepizza_outbox_pending_events Order events not yet published to RabbitMQ.",
        "# TYPE slicepizza_outbox_pending_events gauge",
        f"slicepizza_outbox_pending_events {pending}",
        "# HELP slicepizza_outbox_oldest_pending_age_seconds Age of the oldest unpublished event (0 if none).",
        "# TYPE slicepizza_outbox_oldest_pending_age_seconds gauge",
        f"slicepizza_outbox_oldest_pending_age_seconds {age}",
    ]
    return "\n".join(lines) + "\n"


class MetricsMiddleware:
    """Count every HTTP request and time it (pure ASGI, so it adds almost nothing)."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or scope["path"] == METRICS_PATH:
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        status_code = 500  # if the app raises before answering

        async def send_and_note(message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_and_note)
        finally:
            route = scope.get("route")
            observe_request(
                scope["method"],
                getattr(route, "path", None) or "unmatched",
                status_code,
                time.perf_counter() - started,
            )
