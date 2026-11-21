"""Retention of customers' personal data (Phase 9, ADR 0023).

Name, phone and address are kept to deliver an order, not for ever. Once an
order is finished (delivered or cancelled) and old enough, they are replaced by
a placeholder, **in the order and in its events**: ``order_events.payload``
repeats the customer's name. The order itself, its items and its total stay, so
the pizzeria's numbers do not change. Telegram chat links are removed soon
after the order ends: nothing is sent after that.

Settings (environment):

- ``RETENTION_MONTHS``: months after an order's last change before its personal
  data is replaced. Default 12; ``0`` turns it off.
- ``RETENTION_CHAT_DAYS``: days after an order ends before the Telegram chat
  links of that order are removed. Default 7; ``0`` turns it off.

It runs inside the API, a few times a day, and is safe to repeat and to run in
several API copies (a Postgres advisory lock lets one at a time work). It also
runs by hand::

    docker compose exec api python -m app.retention --dry-run
    docker compose exec api python -m app.retention

Backups of the server keep what they held when they were made, until they
expire: the privacy policy says so.
"""

from __future__ import annotations

import argparse
import copy
import logging
import os
import threading
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Order, OrderEvent, OrderStatus, TelegramSubscription

logger = logging.getLogger(__name__)

REMOVED = "[removed]"
FINISHED = (OrderStatus.DELIVERED, OrderStatus.CANCELLED)
ADVISORY_LOCK_ID = 7_261_104  # any number, different from the outbox relay's
BATCH = 200
RUN_EVERY_SECONDS = 6 * 3600
FIRST_RUN_DELAY_SECONDS = 120


def _int_env(name: str, default: int) -> int:
    try:
        return max(int(os.getenv(name) or default), 0)
    except ValueError:
        return default


def retention_months() -> int:
    return _int_env("RETENTION_MONTHS", 12)


def chat_days() -> int:
    return _int_env("RETENTION_CHAT_DAYS", 7)


def _older_than_months(months: int, now: datetime) -> datetime:
    return now - timedelta(days=round(months * 365 / 12))


def _expired_orders(db: Session, cutoff: datetime):
    """Finished orders last changed before ``cutoff`` whose data is still there."""
    return (
        select(Order.id)
        .where(Order.status.in_(FINISHED), Order.updated_at < cutoff, Order.customer_phone != REMOVED)
        .order_by(Order.id)
    )


def anonymize_old_orders(
    db: Session, months: int, now: datetime | None = None, dry_run: bool = False
) -> tuple[int, int]:
    """Replace the personal data of old finished orders. Returns (orders, events)."""
    now = now or datetime.now(UTC)
    cutoff = _older_than_months(months, now)
    expired = _expired_orders(db, cutoff)
    if dry_run:
        orders = db.scalar(select(func.count()).select_from(expired.subquery()))
        events = db.scalar(
            select(func.count()).select_from(OrderEvent).where(OrderEvent.order_id.in_(expired))
        )
        return int(orders or 0), int(events or 0)

    orders_done = events_done = 0
    while True:
        ids = list(db.scalars(expired.limit(BATCH)))
        if not ids:
            break
        # A Core UPDATE that names updated_at, so its on-update default does not
        # move it to now: the order's age is what decides when it is next looked at.
        db.execute(
            update(Order)
            .where(Order.id.in_(ids))
            .values(
                customer_name=REMOVED,
                customer_phone=REMOVED,
                delivery_address=REMOVED,
                updated_at=Order.updated_at,
            )
        )
        for event in db.scalars(select(OrderEvent).where(OrderEvent.order_id.in_(ids))):
            payload = copy.deepcopy(event.payload)
            payload.setdefault("order", {})["customer_name"] = REMOVED
            payload.setdefault("notify", {})["telegram_chat_ids"] = []
            event.payload = payload  # a new object, so the JSON change is saved
            events_done += 1
        db.execute(delete(TelegramSubscription).where(TelegramSubscription.order_id.in_(ids)))
        db.commit()
        orders_done += len(ids)
    return orders_done, events_done


def remove_old_chat_links(
    db: Session, days: int, now: datetime | None = None, dry_run: bool = False
) -> int:
    """Remove the Telegram chat links of orders that ended ``days`` ago. Returns how many."""
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=days)
    ended = select(Order.id).where(Order.status.in_(FINISHED), Order.updated_at < cutoff)
    if dry_run:
        count = db.scalar(
            select(func.count())
            .select_from(TelegramSubscription)
            .where(TelegramSubscription.order_id.in_(ended))
        )
        return int(count or 0)
    result = db.execute(delete(TelegramSubscription).where(TelegramSubscription.order_id.in_(ended)))
    db.commit()
    return result.rowcount or 0


def run_once(db: Session, now: datetime | None = None, dry_run: bool = False) -> dict[str, int]:
    """One pass of every retention rule that is on. Returns what it did (counts only)."""
    if db.get_bind().dialect.name == "postgresql":
        got_lock = db.scalar(text("SELECT pg_try_advisory_xact_lock(:id)"), {"id": ADVISORY_LOCK_ID})
        if not got_lock:
            db.rollback()
            return {}
    done: dict[str, int] = {}
    months = retention_months()
    if months:
        orders, events = anonymize_old_orders(db, months, now, dry_run)
        done["orders_anonymized"], done["events_anonymized"] = orders, events
    days = chat_days()
    if days:
        done["chat_links_removed"] = remove_old_chat_links(db, days, now, dry_run)
    return done


class RetentionJob:
    """Runs ``run_once`` every few hours in a background thread until ``stop()``."""

    def __init__(
        self, first_delay: float = FIRST_RUN_DELAY_SECONDS, every: float = RUN_EVERY_SECONDS
    ) -> None:
        self._first_delay = first_delay
        self._every = every
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="retention", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        self._thread.join(timeout)

    def _run(self) -> None:
        delay = self._first_delay
        while not self._stop.wait(delay):
            delay = self._every
            try:
                with SessionLocal() as db:
                    done = run_once(db)
                if any(done.values()):
                    logger.info("Retention: %s", done)  # counts only, never personal data
            except Exception as error:  # noqa: BLE001 - never takes the API down
                logger.warning("Retention failed, will retry: %s", type(error).__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Replace old customers' personal data (ADR 0023).")
    parser.add_argument("--dry-run", action="store_true", help="only count what would change")
    args = parser.parse_args()
    with SessionLocal() as db:
        done = run_once(db, dry_run=args.dry_run)
    what = str(done) if done else "nothing (retention is off, or another copy is working)"
    print(("Would change: " if args.dry_run else "Changed: ") + what)


if __name__ == "__main__":
    main()
