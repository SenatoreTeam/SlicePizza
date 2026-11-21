"""Retention of customers' personal data (ADR 0023)."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from app import retention
from app.database import SessionLocal
from app.models import Order, OrderEvent, OrderStatus, TelegramSubscription

ORDER = {
    "customer": {"name": "Ana Souza", "phone": "11999990000", "address": "Rua A, 1"},
    "items": [{"pizza_id": 1, "quantity": 2}],
}
NOW = datetime(2026, 12, 1, tzinfo=UTC)


@pytest.fixture(autouse=True)
def retention_on(monkeypatch):
    monkeypatch.delenv("RETENTION_MONTHS", raising=False)
    monkeypatch.delenv("RETENTION_CHAT_DAYS", raising=False)


def place(client, status="delivered", age_days=0, chat_id=None):
    """An order in ``status`` whose last change was ``age_days`` before NOW."""
    order_id = client.post("/orders", json=ORDER).json()["id"]
    with SessionLocal() as db:
        db.execute(update(Order).where(Order.id == order_id).values(
            status=OrderStatus(status), updated_at=NOW - timedelta(days=age_days)))
        if chat_id:
            db.add(TelegramSubscription(order_id=order_id, chat_id=chat_id))
        db.commit()
    return order_id


def load(order_id):
    with SessionLocal() as db:
        order = db.get(Order, order_id)
        db.expunge(order)
        events = list(db.scalars(select(OrderEvent).where(OrderEvent.order_id == order_id)))
        chats = list(db.scalars(select(TelegramSubscription).where(TelegramSubscription.order_id == order_id)))
        return order, events, chats


def run(**kw):
    with SessionLocal() as db:
        return retention.run_once(db, now=NOW, **kw)


def test_an_old_finished_order_loses_its_personal_data_everywhere(client):
    order_id = place(client, "delivered", age_days=400, chat_id=555)

    done = run()

    order, events, chats = load(order_id)
    assert (order.customer_name, order.customer_phone, order.delivery_address) == ("[removed]",) * 3
    assert events and all(e.payload["order"]["customer_name"] == "[removed]" for e in events)
    assert all(e.payload["notify"]["telegram_chat_ids"] == [] for e in events)
    assert chats == []
    assert done["orders_anonymized"] == 1 and done["events_anonymized"] >= 1


def test_the_order_itself_is_kept_for_the_numbers(client):
    order_id = place(client, "delivered", age_days=400)
    run()
    order, _, _ = load(order_id)
    assert order.total_cents > 0 and order.status == OrderStatus.DELIVERED
    with SessionLocal() as db:
        assert db.get(Order, order_id).items


def test_the_age_of_the_order_does_not_move(client):
    order_id = place(client, "cancelled", age_days=400)
    run()
    order, _, _ = load(order_id)
    updated = order.updated_at.replace(tzinfo=UTC)
    assert updated == NOW - timedelta(days=400)


def test_a_recent_order_is_untouched(client):
    order_id = place(client, "delivered", age_days=30)
    run()
    order, _, _ = load(order_id)
    assert order.customer_phone == "11999990000"


def test_an_open_order_is_never_anonymized_however_old(client):
    order_id = place(client, "preparing", age_days=900)
    run()
    order, _, _ = load(order_id)
    assert order.customer_name == "Ana Souza"


def test_it_is_safe_to_repeat(client):
    place(client, "delivered", age_days=400)
    assert run()["orders_anonymized"] == 1
    assert run()["orders_anonymized"] == 0


def test_dry_run_changes_nothing_and_counts(client):
    order_id = place(client, "delivered", age_days=400)
    done = run(dry_run=True)
    order, _, _ = load(order_id)
    assert order.customer_phone == "11999990000"
    assert done["orders_anonymized"] == 1


def test_chat_links_go_a_week_after_the_order_ends_but_the_order_keeps_its_data(client):
    ended = place(client, "delivered", age_days=10, chat_id=111)
    open_order = place(client, "preparing", age_days=10, chat_id=222)
    recent = place(client, "delivered", age_days=2, chat_id=333)

    done = run()

    assert load(ended)[2] == [] and load(ended)[0].customer_name == "Ana Souza"
    assert len(load(open_order)[2]) == 1 and len(load(recent)[2]) == 1
    assert done["chat_links_removed"] == 1


def test_months_zero_turns_the_anonymization_off(client, monkeypatch):
    monkeypatch.setenv("RETENTION_MONTHS", "0")
    order_id = place(client, "delivered", age_days=900)
    done = run()
    assert "orders_anonymized" not in done
    assert load(order_id)[0].customer_name == "Ana Souza"


def test_days_zero_turns_the_chat_cleanup_off(client, monkeypatch):
    monkeypatch.setenv("RETENTION_CHAT_DAYS", "0")
    order_id = place(client, "delivered", age_days=10, chat_id=111)
    assert "chat_links_removed" not in run()
    assert len(load(order_id)[2]) == 1


def test_a_bad_setting_falls_back_to_the_default(monkeypatch):
    monkeypatch.setenv("RETENTION_MONTHS", "twelve")
    assert retention.retention_months() == 12
