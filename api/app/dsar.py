"""A customer's own request about their data (Phase 9, ADR 0023).

LGPD Art. 18: a customer can ask what we keep (access) and ask for it to be
erased. The pizzeria runs these by hand, from ``docs/PRIVACY-REQUESTS.md``::

    docker compose exec api python -m app.dsar export --phone "11 99999-0000"
    docker compose exec api python -m app.dsar erase  --phone "11 99999-0000"            # shows what would change
    docker compose exec api python -m app.dsar erase  --phone "11 99999-0000" --confirm  # does it

Orders are found by phone number, ignoring spaces, dashes and a leading +55.
**The output of ``export`` is personal data**: it goes to the customer only.

``erase`` uses the same replacement as the retention job. It refuses while the
customer has an order still in progress (the kitchen needs the address): finish
or cancel it first. Items and totals stay (the pizzeria's own numbers); backups
of the server keep older copies until they expire.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .database import SessionLocal
from .models import Order, TelegramSubscription
from .retention import FINISHED, REMOVED, anonymize_ids

MIN_DIGITS = 8  # a shorter number would match strangers


def digits(phone: str) -> str:
    """Only the digits, without Brazil's country code: ``+55 (11) 99999-0000`` -> ``11999990000``."""
    number = re.sub(r"\D", "", phone)
    if number.startswith("55") and len(number) > 11:
        number = number[2:]
    return number


def find_orders(db: Session, phone: str) -> list[Order]:
    """The customer's orders, oldest first, whose data was not replaced yet."""
    wanted = digits(phone)
    if len(wanted) < MIN_DIGITS:
        raise ValueError(f"The phone number needs at least {MIN_DIGITS} digits.")
    orders = db.scalars(
        select(Order)
        .where(Order.customer_phone != REMOVED)
        .options(selectinload(Order.items))
        .order_by(Order.created_at, Order.id)
    )
    found = []
    for order in orders:
        stored = digits(order.customer_phone)
        if stored and (stored.endswith(wanted) or wanted.endswith(stored)):
            found.append(order)
    return found


def export(db: Session, phone: str) -> dict:
    """Everything we keep about this phone number, as the customer may receive it."""
    orders = find_orders(db, phone)
    ids = [order.id for order in orders]
    chats = list(
        db.scalars(select(TelegramSubscription).where(TelegramSubscription.order_id.in_(ids)))
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "orders": [
            {
                "id": order.id,
                "placed_at": order.created_at.isoformat(),
                "status": order.status.value,
                "name": order.customer_name,
                "phone": order.customer_phone,
                "delivery_address": order.delivery_address,
                "total_cents": order.total_cents,
                "items": [
                    {"pizza": item.pizza.name, "quantity": item.quantity} for item in order.items
                ],
            }
            for order in orders
        ],
        "telegram_chat_ids": sorted({chat.chat_id for chat in chats}),
    }


def erase(db: Session, phone: str, confirm: bool) -> dict:
    """Replace this customer's data. Without ``confirm`` it only says what would change."""
    orders = find_orders(db, phone)
    open_orders = [order.id for order in orders if order.status not in FINISHED]
    result = {"orders": len(orders), "open_orders": open_orders, "done": False, "events": 0}
    if open_orders or not orders or not confirm:
        return result
    result["events"] = anonymize_ids(db, [order.id for order in orders])
    db.commit()
    result["done"] = True
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="A customer's request about their data (LGPD Art. 18)."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("export", "print what we keep"), ("erase", "replace the customer's data")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--phone", required=True, help="the phone number the customer ordered with")
    commands.choices["erase"].add_argument(
        "--confirm", action="store_true", help="really do it (without it, only shows what would change)"
    )
    args = parser.parse_args(argv)

    try:
        with SessionLocal() as db:
            if args.command == "export":
                print(json.dumps(export(db, args.phone), indent=2, ensure_ascii=False))
                return 0
            result = erase(db, args.phone, args.confirm)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    if not result["orders"]:
        print("No order with that phone number holds personal data.")
        return 0
    if result["open_orders"]:
        waiting = ", ".join(result["open_orders"])
        print(f"Not done: {len(result['open_orders'])} order(s) still in progress ({waiting}).")
        print("Finish or cancel them in the kitchen first, then run this again.")
        return 1
    if result["done"]:
        print(
            f"Done: {result['orders']} order(s) and {result['events']} event(s) replaced. "
            "Items and totals were kept."
        )
    else:
        print(f"Would replace {result['orders']} order(s). Run again with --confirm to do it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
