"""The kitchen's login, lockout and session (ADR 0024)."""

import base64
import os
import time

import bcrypt
import pytest
from fastapi.testclient import TestClient

from app import kitchen_login
from app.main import app

PASSWORD = "forno-a-lenha-42"
# Cost 4, the lowest: the real hash (`caddy hash-password`) is 14, too slow for tests.
HASH = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
OTHER_HASH = bcrypt.hashpw(b"another-password", bcrypt.gensalt(rounds=4)).decode()
TOKEN = os.environ["KITCHEN_API_TOKEN"]

ORDER = {
    "customer": {"name": "Zé", "phone": "+55 11 99999-0000", "address": "Rua das Pizzas, 42"},
    "items": [{"pizza_id": 1, "quantity": 1}],
}


@pytest.fixture(autouse=True)
def fresh_guard():
    kitchen_login.guard.reset()
    yield
    kitchen_login.guard.reset()


def through_caddy(password_hash=HASH, token=TOKEN, **extra):
    """The headers Caddy's /kitchen/api route adds."""
    return {"X-Kitchen-Proxy": token, "X-Kitchen-Password-Hash": password_hash, **extra}


@pytest.fixture
def board():
    """A browser on the kitchen board: every call goes through Caddy's kitchen route."""
    return TestClient(app, headers=through_caddy())


def log_in(client, password=PASSWORD, headers=None):
    return client.post("/session", json={"password": password}, headers=headers)


def session_cookie(response):
    """The cookie's value. (The test client won't send a Secure cookie over http.)"""
    return response.cookies[kitchen_login.COOKIE]


# --- Logging in ----------------------------------------------------------------------


def test_the_right_password_gives_a_12_hour_session_cookie(board):
    response = log_in(board)

    assert response.status_code == 200
    set_cookie = response.headers["set-cookie"].lower()
    for attribute in ("httponly", "secure", "samesite=strict", "path=/kitchen", "max-age=43200"):
        assert attribute in set_cookie
    assert "expires_at" in response.json()


def test_a_wrong_password_is_refused(board):
    response = log_in(board, "pepperoni")

    assert response.status_code == 401
    assert kitchen_login.COOKIE not in response.cookies


def test_the_hash_may_come_base64_encoded_as_docs_deploy_recommends(client):
    encoded = base64.b64encode(HASH.encode()).decode()

    assert log_in(client, headers=through_caddy(encoded)).status_code == 200


def test_the_login_only_exists_on_the_kitchen_route(client):
    # The public /api never adds the kitchen token: the route looks absent.
    assert log_in(client).status_code == 404
    assert log_in(client, headers=through_caddy(token="x" * 40)).status_code == 404
    assert client.delete("/session").status_code == 404


def test_without_a_password_hash_the_login_says_it_is_not_set_up(client):
    for bad in ("", "not-a-hash", "$2a$14$too-short"):
        response = log_in(client, headers=through_caddy(bad))
        assert response.status_code == 503
        assert "KITCHEN_PASSWORD_HASH" in response.json()["detail"]


def test_a_login_posted_as_a_form_is_refused(board):
    # What a form on another site would send.
    response = board.post("/session", data={"password": PASSWORD})

    assert response.status_code in (415, 422)


# --- Lockout ---------------------------------------------------------------------------


def test_five_wrong_passwords_lock_the_address_even_for_the_right_one(board):
    for _ in range(kitchen_login.MAX_FAILURES - 1):
        assert log_in(board, "wrong").status_code == 401

    locked = log_in(board, "wrong")
    assert locked.status_code == 429
    assert int(locked.headers["retry-after"]) > 14 * 60

    still = log_in(board)  # the right password, while locked
    assert still.status_code == 429
    assert kitchen_login.COOKIE not in still.cookies


def test_a_locked_address_does_not_cost_a_password_check(board, monkeypatch):
    for _ in range(kitchen_login.MAX_FAILURES):
        log_in(board, "wrong")
    calls = []
    monkeypatch.setattr(kitchen_login.bcrypt, "checkpw", lambda *a: calls.append(a) or True)

    assert log_in(board).status_code == 429
    assert calls == []


def test_a_good_login_clears_the_count(board):
    for _ in range(kitchen_login.MAX_FAILURES - 1):
        log_in(board, "wrong")
    assert log_in(board).status_code == 200

    for _ in range(kitchen_login.MAX_FAILURES - 1):
        assert log_in(board, "wrong").status_code == 401


def test_the_lockout_counts_per_address_and_ends():
    guard = kitchen_login.LoginGuard(max_failures=3, lock_seconds=60)
    for second in range(3):
        guard.failed("10.0.0.1", now=100 + second)

    assert guard.wait("10.0.0.1", now=103) > 0
    assert guard.wait("10.0.0.2", now=103) == 0  # someone else is not locked
    assert guard.wait("10.0.0.1", now=163) == 0  # 60 s after the lock


def test_old_failures_are_forgotten():
    guard = kitchen_login.LoginGuard(max_failures=3, lock_seconds=60)
    guard.failed("10.0.0.1", now=0)
    guard.failed("10.0.0.1", now=1)

    assert guard.failed("10.0.0.1", now=100) is False  # the first two are over 60 s old


# --- The session ---------------------------------------------------------------------------


def test_the_session_opens_the_order_list_and_status_changes(board, client):
    order = client.post("/orders", json=ORDER).json()
    cookie = session_cookie(log_in(board))
    headers = {"Cookie": f"{kitchen_login.COOKIE}={cookie}"}

    listed = board.get("/orders", headers=headers)
    assert listed.status_code == 200
    assert [o["id"] for o in listed.json()] == [order["id"]]

    moved = board.patch(f"/orders/{order['id']}/status", json={"status": "preparing"}, headers=headers)
    assert moved.status_code == 200


def test_without_a_session_the_board_gets_401(board):
    assert board.get("/orders").status_code == 401


def test_the_cookie_does_nothing_on_the_public_route(board, client):
    cookie = session_cookie(log_in(board))

    response = client.get("/orders", headers={"Cookie": f"{kitchen_login.COOKIE}={cookie}"})

    assert response.status_code == 401


def test_a_status_change_sent_as_a_form_is_refused(board, client):
    order = client.post("/orders", json=ORDER).json()
    cookie = session_cookie(log_in(board))

    response = board.patch(
        f"/orders/{order['id']}/status",
        content="status=preparing",
        headers={
            "Cookie": f"{kitchen_login.COOKIE}={cookie}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    assert response.status_code == 415


def test_changing_the_password_logs_every_device_out(board, client):
    cookie = session_cookie(log_in(board))

    response = client.get(
        "/orders",
        headers=through_caddy(OTHER_HASH, Cookie=f"{kitchen_login.COOKIE}={cookie}"),
    )

    assert response.status_code == 401


def test_a_session_ends_after_12_hours():
    hashed = HASH.encode()
    value, expires = kitchen_login.new_session(hashed, now=1_000)

    assert expires == 1_000 + 12 * 3600
    assert kitchen_login.session_is_valid(value, hashed, now=expires - 1)
    assert not kitchen_login.session_is_valid(value, hashed, now=expires)


def test_a_changed_cookie_is_not_valid():
    hashed = HASH.encode()
    value, expires = kitchen_login.new_session(hashed)
    signature = value.partition(".")[2]

    assert kitchen_login.session_is_valid(value, hashed)
    assert not kitchen_login.session_is_valid(f"{expires + 3600}.{signature}", hashed)
    assert not kitchen_login.session_is_valid(f"{expires}.{'0' * 64}", hashed)
    for junk in (None, "", "abc", "123", ".abc"):
        assert not kitchen_login.session_is_valid(junk, hashed)


def test_logging_out_removes_the_cookie(board):
    log_in(board)

    response = board.delete("/session")

    assert response.status_code == 204
    set_cookie = response.headers["set-cookie"].lower()
    assert kitchen_login.COOKIE in set_cookie
    assert "max-age=0" in set_cookie
    assert "path=/kitchen" in set_cookie


def test_scripts_keep_using_the_token(kitchen):
    assert kitchen.get("/orders").status_code == 200


def test_nothing_secret_is_logged(board, caplog):
    log_in(board, "wrong")
    log_in(board)

    assert PASSWORD not in caplog.text
    assert "wrong" not in caplog.text.replace("wrong password", "")
    assert HASH not in caplog.text


def test_the_signature_uses_the_server_secret(monkeypatch):
    hashed = HASH.encode()
    value, _ = kitchen_login.new_session(hashed, now=time.time())
    monkeypatch.setattr(kitchen_login.settings, "kitchen_api_token", "y" * 40)

    assert not kitchen_login.session_is_valid(value, hashed)
