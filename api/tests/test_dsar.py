"""A customer's own request: access and erasure (ADR 0023)."""

import pytest
from sqlalchemy import select, update

from app import dsar
from app.database import SessionLocal
from app.models import Order, OrderEvent, OrderStatus, TelegramSubscription

ORDER = {
    "customer": {"name": "Ana Souza", "phone": "+55 (11) 99999-0000", "address": "Rua A, 1"},
    "items": [{"pizza_id": 1, "quantity": 2}],
}


def place(client, phone="+55 (11) 99999-0000", status="delivered", chat_id=None):
    body = {**ORDER, "customer": {**ORDER["customer"], "phone": phone}}
    order_id = client.post("/orders", json=body).json()["id"]
    with SessionLocal() as db:
        db.execute(update(Order).where(Order.id == order_id).values(status=OrderStatus(status)))
        if chat_id:
            db.add(TelegramSubscription(order_id=order_id, chat_id=chat_id))
        db.commit()
    return order_id


def phones():
    with SessionLocal() as db:
        return list(db.scalars(select(Order.customer_phone)))


def test_digits_ignore_punctuation_and_the_country_code():
    assert dsar.digits("+55 (11) 99999-0000") == "11999990000"
    assert dsar.digits("11 99999 0000") == "11999990000"


def test_a_short_number_is_refused(client):
    with SessionLocal() as db, pytest.raises(ValueError):
        dsar.find_orders(db, "123")


def test_export_gives_the_customer_everything_we_keep(client):
    place(client, chat_id=777)
    place(client, phone="11 90000-1111")  # another customer: must not appear

    with SessionLocal() as db:
        data = dsar.export(db, "11999990000")

    assert len(data["orders"]) == 1
    order = data["orders"][0]
    assert order["name"] == "Ana Souza" and order["delivery_address"] == "Rua A, 1"
    assert order["items"] == [{"pizza": "Margherita", "quantity": 2}]
    assert data["telegram_chat_ids"] == [777]


def test_the_number_may_be_written_differently_in_the_request(client):
    place(client)
    with SessionLocal() as db:
        assert len(dsar.export(db, "(11) 99999-0000")["orders"]) == 1
        assert len(dsar.export(db, "+5511999990000")["orders"]) == 1


def test_erase_without_confirm_changes_nothing(client):
    place(client)
    with SessionLocal() as db:
        result = dsar.erase(db, "11999990000", confirm=False)
    assert result["orders"] == 1 and result["done"] is False
    assert "[removed]" not in phones()


def test_erase_replaces_the_orders_events_and_chat_links_of_that_customer_only(client):
    mine = place(client, chat_id=777)
    other = place(client, phone="11 90000-1111", chat_id=888)

    with SessionLocal() as db:
        result = dsar.erase(db, "11999990000", confirm=True)

    assert result["done"] and result["orders"] == 1
    with SessionLocal() as db:
        assert db.get(Order, mine).customer_name == "[removed]"
        assert db.get(Order, other).customer_name == "Ana Souza"
        events = list(db.scalars(select(OrderEvent).where(OrderEvent.order_id == mine)))
        assert events and all(e.payload["order"]["customer_name"] == "[removed]" for e in events)
        chats = list(db.scalars(select(TelegramSubscription.order_id)))
        assert chats == [other]


def test_erase_refuses_while_an_order_is_in_progress(client):
    place(client, status="delivered")
    place(client, status="preparing")
    with SessionLocal() as db:
        result = dsar.erase(db, "11999990000", confirm=True)
    assert result["done"] is False and len(result["open_orders"]) == 1
    assert "[removed]" not in phones()


def test_a_second_erase_finds_nothing_left(client):
    place(client)
    with SessionLocal() as db:
        dsar.erase(db, "11999990000", confirm=True)
    with SessionLocal() as db:
        assert dsar.erase(db, "11999990000", confirm=True)["orders"] == 0


def test_the_command_line_says_what_it_did(client, capsys):
    place(client)
    assert dsar.main(["erase", "--phone", "11999990000"]) == 0
    assert "Would replace 1 order" in capsys.readouterr().out
    assert dsar.main(["erase", "--phone", "11999990000", "--confirm"]) == 0
    assert "Done: 1 order" in capsys.readouterr().out
    assert dsar.main(["export", "--phone", "11999990000"]) == 0
    assert capsys.readouterr().out.count('"id"') == 0  # nothing left to export
    assert dsar.main(["export", "--phone", "123"]) == 2
