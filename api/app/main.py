"""Orders API: menu, orders and order status updates."""

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import TypeAdapter
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from . import cache
from .auth import require_kitchen
from .config import settings
from .database import Base, SessionLocal, engine, get_db, wait_for_database
from .events import ORDER_CREATED, ORDER_STATUS_CHANGED, record_event
from .internal import router as internal_router
from .models import ALLOWED_TRANSITIONS, Order, OrderEvent, OrderItem, OrderStatus, Pizza
from .outbox import OutboxRelay, RabbitMQPublisher
from .ratelimit import limit_orders
from .retention import RetentionJob
from .schemas import OrderCreate, OrderOut, OrderPublicOut, OrderStatusUpdate, PizzaOut
from .seed import seed_menu

logger = logging.getLogger(__name__)


def _configure_app_logging() -> None:
    """Show the app's own log lines (app.*) next to Uvicorn's.

    Uvicorn only configures its own loggers. Without a handler, Python printed
    the app's warnings bare and dropped its INFO lines, such as the outbox
    relay's "Published 2 order event(s)". Propagation stays on, so pytest's
    caplog still sees them.
    """
    app_logger = logging.getLogger("app")
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s: %(message)s"))
        app_logger.addHandler(handler)
        app_logger.setLevel(logging.INFO)


_configure_app_logging()


# Publishes the outbox to RabbitMQ when RABBITMQ_HOST is set (ADR 0004).
relay: OutboxRelay | None = None
# Replaces old customers' personal data (ADR 0023).
retention: RetentionJob | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global relay, retention
    # Phase 1 keeps the schema simple: create the tables on startup and seed
    # the menu. Migrations (Alembic) arrive when the schema starts to evolve.
    await wait_for_database()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_menu(db)
    cache.clear_menu()  # the menu may have changed: never serve the old one

    if settings.rabbitmq is not None:
        rabbitmq = settings.rabbitmq
        relay = OutboxRelay(SessionLocal, lambda: RabbitMQPublisher(rabbitmq))
        relay.start()
    else:
        logger.warning(
            "RABBITMQ_HOST is not set: order events are kept in order_events "
            "and published once RabbitMQ is configured."
        )
    retention = RetentionJob()
    retention.start()
    try:
        yield
    finally:
        if relay is not None:
            relay.stop()
            relay = None
        retention.stop()
        retention = None


def _events_committed() -> None:
    """Tell the relay there is something new to publish."""
    if relay is not None:
        relay.wake()


app = FastAPI(
    title="SlicePizza Orders API",
    description="Menu and orders for Zé's Pizzeria.",
    # The version (releases.toml, ADR 0010), set by the pipeline when it builds the image.
    version=os.getenv("APP_VERSION") or "unknown",
    lifespan=lifespan,
)


class UnhandledErrorAsJSON:
    """Turn an unhandled exception into a JSON 500 *inside* CORSMiddleware.

    Starlette answers unhandled exceptions in ServerErrorMiddleware, which sits
    outside every middleware added here, so its 500 would carry no CORS
    header and the browser would report a CORS error instead of the 500.
    Added before CORSMiddleware, this one runs inside it.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_and_track(message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_and_track)
        except Exception:
            if response_started:
                raise  # too late to send another response
            logger.exception("Unhandled error on %s %s", scope["method"], scope["path"])
            response = JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
            await response(scope, receive, send)


if settings.cors_origins:
    # Off by default: in production the site and the API share one origin
    # (ADR 0003), so browsers need no CORS. CORS_ORIGINS is for a site served
    # from another origin, e.g. a local `python3 -m http.server 8080` against
    # the API on port 8000. Browsers then send an OPTIONS preflight before
    # every POST and PATCH that carries JSON, and only the configured origins
    # get an answer. No cookies are used, so credentials stay disabled.
    #
    # Middleware added last runs first: CORSMiddleware wraps
    # UnhandledErrorAsJSON, so even a 500 carries the CORS header.
    app.add_middleware(UnhandledErrorAsJSON)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH"],
        # Starlette always allows the CORS-safelisted Accept, Accept-Language,
        # Content-Language and Content-Type; listed here to make the intent
        # explicit, since every POST and PATCH sends application/json.
        allow_headers=["Content-Type"],
        max_age=600,
    )


# Routes for the notification worker (ADR 0006): off without INTERNAL_API_TOKEN.
app.include_router(internal_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> Response:
    """Same 422 body as FastAPI's default handler, but JSON-escaped as ASCII.

    The error echoes the invalid input back. If that input is not valid
    Unicode (e.g. a lone surrogate "\\ud800"), the default handler crashes
    while encoding its own response and returns 500. ASCII-escaped JSON
    ("\\u00e9" instead of "é") is equivalent for any JSON client.
    """
    body = json.dumps({"detail": jsonable_encoder(exc.errors())}, ensure_ascii=True)
    return Response(content=body, status_code=422, media_type="application/json")


# SQLSTATE codes that mean "cannot talk to the server", as opposed to a bug,
# a deadlock or a timeout: class 08 (connection exception), admin shutdown,
# crash shutdown and "the database system is starting up".
# Note: errors raised while *connecting* (refused, timeout, DNS, wrong password,
# unknown database, too many connections) carry no SQLSTATE at all.
_UNAVAILABLE_SQLSTATES = ("08", "57P01", "57P02", "57P03")


def is_database_unavailable(exc: OperationalError) -> bool:
    """True only when the error means the database cannot be reached."""
    if exc.connection_invalidated:
        return True
    if not hasattr(exc.orig, "sqlstate"):
        # Not a psycopg error (e.g. SQLite in the tests): a real error.
        return False
    sqlstate = exc.orig.sqlstate
    # No SQLSTATE: the connection could not be established (see above).
    return sqlstate is None or sqlstate.startswith(_UNAVAILABLE_SQLSTATES)


@app.exception_handler(OperationalError)
async def database_error(request: Request, exc: OperationalError) -> JSONResponse:
    """Return 503 when the database is unreachable, 500 for anything else."""
    if is_database_unavailable(exc):
        # Log the cause: "unavailable" can also mean a wrong password or an
        # unknown database, which nobody could diagnose from the 503 alone.
        logger.warning(
            "Database unavailable on %s %s: %s",
            request.method,
            request.url.path,
            exc.orig,
        )
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    logger.error("Database error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


def _load_order(db: Session, order_id: uuid.UUID, for_update: bool = False) -> Order:
    query = (
        select(Order)
        .where(Order.id == str(order_id))
        .options(selectinload(Order.items).selectinload(OrderItem.pizza))
    )
    if for_update:
        # SELECT ... FOR UPDATE: lock the order row until this transaction
        # ends. (SQLite has no row locks; it is only used for dev and tests.)
        query = query.with_for_update()
    order = db.scalar(query)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# An unpublished event older than this means the outbox is stuck: the relay
# publishes within a second or two, and retries at most every 30 s.
OUTBOX_LATE_SECONDS = 300


def _outbox_oldest_seconds(db: Session) -> int | None:
    """Age in seconds of the oldest unpublished event, or None when none waits."""
    created = db.scalar(
        select(OrderEvent.created_at)
        .where(OrderEvent.published_at.is_(None))
        .order_by(OrderEvent.id)  # the partial index on unpublished ids
        .limit(1)
    )
    if created is None:
        return None
    if created.tzinfo is None:  # SQLite keeps UTC without a time zone
        created = created.replace(tzinfo=UTC)
    return max(0, int((datetime.now(UTC) - created).total_seconds()))


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str | int | None]:
    """Report whether the API can reach the database, which version it runs,
    and whether order events are leaving the outbox (roadmap 12.5).

    ``version`` is the commit the image was built from (``GIT_COMMIT``, set by
    the pipeline, ADR 0008), and ``release`` the version number (``APP_VERSION``,
    from releases.toml, ADR 0010); each is ``unknown`` outside an image built by CI.

    ``outbox`` is ``ok``, ``late`` (an event has waited more than
    ``OUTBOX_LATE_SECONDS``: RabbitMQ or the relay is stuck) or ``off``
    (``RABBITMQ_HOST`` is not set, so events wait on purpose), and
    ``outbox_oldest_seconds`` the age of the oldest unpublished event (null
    when none waits). A late outbox does **not** fail the check: the status
    code only says whether the API works, so the deploy and Docker do not roll
    back or restart the API over a RabbitMQ problem. Monitors read the field.
    """
    try:
        db.execute(text("SELECT 1"))
        oldest = _outbox_oldest_seconds(db)
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    if settings.rabbitmq is None:
        outbox = "off"
    elif oldest is not None and oldest > OUTBOX_LATE_SECONDS:
        outbox = "late"
    else:
        outbox = "ok"
    return {
        "status": "ok",
        "database": "ok",
        "outbox": outbox,
        "outbox_oldest_seconds": oldest,
        "version": os.getenv("GIT_COMMIT") or "unknown",
        "release": os.getenv("APP_VERSION") or "unknown",
    }


# A cached menu must have this shape to be served (ADR 0019): during a deploy
# with several API copies (ADR 0020), an older copy may write another one.
_MENU = TypeAdapter(list[PizzaOut])


@app.get("/menu", response_model=list[PizzaOut])
def get_menu(db: Session = Depends(get_db)) -> list[dict]:
    """List the pizzas on the menu (from Redis when it is on, ADR 0019)."""
    cached = cache.get_menu(check=_MENU.validate_python)
    if cached is not None:
        return cached
    pizzas = db.scalars(select(Pizza).order_by(Pizza.id))
    menu = [PizzaOut.model_validate(pizza).model_dump(mode="json") for pizza in pizzas]
    cache.set_menu(menu)
    return menu


@app.post(
    "/orders",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_orders)],
    responses={429: {"description": "Too many orders from this address (ADR 0021)"}},
)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)) -> Order:
    """Create an order, pricing it from the menu in the database."""
    pizza_ids = {item.pizza_id for item in payload.items}
    pizzas = {
        pizza.id: pizza
        for pizza in db.scalars(select(Pizza).where(Pizza.id.in_(pizza_ids)))
    }

    missing = sorted(pizza_ids - pizzas.keys())
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Pizza(s) not found: {missing}",
        )

    unavailable = sorted(
        pizza.name for pizza in pizzas.values() if not pizza.available
    )
    if unavailable:
        raise HTTPException(
            status_code=409,
            detail=f"Pizza(s) unavailable: {unavailable}",
        )

    order = Order(
        customer_name=payload.customer.name,
        customer_phone=payload.customer.phone,
        delivery_address=payload.customer.address,
        status=OrderStatus.RECEIVED,
        total_cents=sum(
            pizzas[item.pizza_id].price_cents * item.quantity
            for item in payload.items
        ),
    )
    for item in payload.items:
        pizza = pizzas[item.pizza_id]
        order.items.append(
            OrderItem(
                pizza=pizza,
                quantity=item.quantity,
                unit_price_cents=pizza.price_cents,
            )
        )

    db.add(order)
    # Same transaction: the order and its event are saved together or not at all.
    record_event(db, order, ORDER_CREATED)
    # The INSERT ... RETURNING already fills created_at/updated_at, and the
    # items and pizzas are in memory, so no refresh is needed.
    db.commit()
    _events_committed()
    return order


# What the kitchen board shows by default: orders that still need someone.
OPEN_STATUSES = (OrderStatus.RECEIVED, OrderStatus.PREPARING, OrderStatus.OUT_FOR_DELIVERY)
MAX_LISTED_ORDERS = 500


@app.get(
    "/orders",
    response_model=list[OrderOut],
    dependencies=[Depends(require_kitchen)],
    responses={401: {"description": "Kitchen only"}},
)
def list_orders(
    status_filter: list[OrderStatus] | None = Query(
        default=None,
        alias="status",
        description="Only these statuses (repeat the parameter for several). "
        "Default: the open ones (received, preparing, out_for_delivery).",
    ),
    limit: int = Query(default=200, ge=1, le=MAX_LISTED_ORDERS),
    db: Session = Depends(get_db),
) -> list[Order]:
    """List orders for the kitchen, oldest first. Kitchen only (ADR 0007)."""
    statuses = status_filter or OPEN_STATUSES
    query = (
        select(Order)
        .where(Order.status.in_(statuses))
        .order_by(Order.created_at, Order.id)
        .limit(limit)
        .options(selectinload(Order.items).selectinload(OrderItem.pizza))
    )
    return list(db.scalars(query))


@app.get("/orders/{order_id}", response_model=OrderPublicOut)
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)) -> Order:
    """Get an order's progress and items, for whoever has its link (ADR 0022).

    No name, phone or address: those are only in the answer to the request that
    created the order, and in the kitchen's routes.
    """
    return _load_order(db, order_id)


@app.patch(
    "/orders/{order_id}/status",
    response_model=OrderOut,
    dependencies=[Depends(require_kitchen)],
    responses={401: {"description": "Kitchen only"}},
)
def update_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
) -> Order:
    """Move an order to the next status. Kitchen only (ADR 0007).

    Allowed path: received -> preparing -> out_for_delivery -> delivered,
    and received -> cancelled. Repeating the current status is a no-op.

    The order row is locked while we check and change it, so concurrent
    requests for the same order run one after the other: each one sees the
    status the previous one committed. Two identical requests both get 200,
    and two conflicting ones get 200 and 409.
    """
    order = _load_order(db, order_id, for_update=True)

    if payload.status == order.status:
        return order

    allowed = ALLOWED_TRANSITIONS[order.status]
    if payload.status not in allowed:
        allowed_names = ", ".join(sorted(s.value for s in allowed)) or "none"
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot change status from '{order.status.value}' "
                f"to '{payload.status.value}'. Allowed: {allowed_names}"
            ),
        )

    previous_status = order.status
    order.status = payload.status
    # Same transaction as the status change (the outbox, ADR 0004). A no-op
    # (same status) and a 409 returned above add no event.
    record_event(db, order, ORDER_STATUS_CHANGED, previous_status=previous_status)
    # The UPDATE returns the new updated_at (eager_defaults on Order), so the
    # response shows exactly what this request wrote, with no extra SELECT.
    db.commit()
    _events_committed()
    return order
