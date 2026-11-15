"""Wait for a deploy to go live, then check the live system (ADR 0009).

Used by the pipeline after it asks the server to deploy a version:

    python3 -I .github/scripts/check_deploy.py https://staging.slicepizza.senatore.tech <commit> --write
    python3 -I .github/scripts/check_deploy.py https://slicepizza.senatore.tech <commit>

1. Waits (up to --timeout seconds) until the web container's /version and the
   API's /api/health both report <commit>: the deploy is asynchronous, so the
   old version answers for a while.
2. Checks what any visitor sees: the menu site, the menu, the API docs, and
   that the private routes stay private (/kitchen asks for a login, listing or
   changing orders without the kitchen's token is refused, /api/internal is
   not reachable).
3. With --write (staging only, never production): places an order and reads
   it back like a customer. With KITCHEN_PASSWORD in the environment, also
   logs in to the kitchen board, finds the order and moves it to "preparing".

Exit code 0 when everything passed, 1 otherwise. Standard library only: it
runs on the runner's python3 without installing anything.
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

USER_AGENT = "slicepizza-deploy-check"


class CheckFailed(Exception):
    pass


def request(method, url, body=None, headers=None, timeout=15):
    """Return (status, text) for a request; never raises on an HTTP error."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", USER_AGENT)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for name, value in (headers or {}).items():
        req.add_header(name, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")


def get_json(url, headers=None, expect=200):
    status, text = request("GET", url, headers=headers)
    if status != expect:
        raise CheckFailed(f"GET {url}: expected {expect}, got {status}: {text[:200]}")
    return json.loads(text)


def expect_status(method, url, expected, body=None, headers=None):
    status, text = request(method, url, body=body, headers=headers)
    if status != expected:
        raise CheckFailed(f"{method} {url}: expected {expected}, got {status}: {text[:200]}")
    print(f"ok  {method} {url} -> {status}")
    return text


def live_versions(base):
    """What /version and /api/health report right now (None if unreachable)."""
    web = api = None
    try:
        status, text = request("GET", f"{base}/version", timeout=10)
        # A commit is one short line; anything else (an HTML page from an
        # older image or another site) is shown shortened.
        text = text.strip()
        if status == 200:
            web = text if len(text) <= 64 and "\n" not in text else f"<not a version: {text[:40]!r}...>"
        else:
            web = f"<HTTP {status}>"
    except OSError:
        pass
    try:
        status, text = request("GET", f"{base}/api/health", timeout=10)
        if status == 200:
            health = json.loads(text)
            if health.get("status") == "ok":
                api = health.get("version")
        else:
            api = f"<HTTP {status}>"
    except (OSError, ValueError):
        pass
    return web, api


def wait_for_version(base, version, timeout):
    deadline = time.monotonic() + timeout
    last = None
    while True:
        current = live_versions(base)
        if current != last:
            print(f"live: web={current[0]} api={current[1]}")
            last = current
        if current == (version, version):
            print(f"ok  {base} runs {version}")
            return
        if time.monotonic() > deadline:
            raise CheckFailed(
                f"{base} still reports web={current[0]} api={current[1]} after {timeout} s, "
                f"not {version}. Check the deployment's log in Dokploy."
            )
        time.sleep(10)


def check_public(base):
    page = expect_status("GET", f"{base}/", 200)
    if "Pizzeria" not in page:
        raise CheckFailed(f"GET {base}/ does not look like the menu site")
    menu = get_json(f"{base}/api/menu")
    if not isinstance(menu, list) or not menu:
        raise CheckFailed(f"GET {base}/api/menu: expected a non-empty list, got {menu!r:.200}")
    print(f"ok  GET {base}/api/menu -> {len(menu)} pizzas")
    expect_status("GET", f"{base}/api/docs", 200)
    # Private routes stay private (ADR 0006, ADR 0007).
    expect_status("GET", f"{base}/kitchen/", 401)
    expect_status("GET", f"{base}/api/orders", 401)
    expect_status(
        "PATCH",
        f"{base}/api/orders/00000000-0000-0000-0000-000000000000/status",
        401,
        body={"status": "preparing"},
    )
    expect_status("PUT", f"{base}/api/internal/orders/x/telegram-subscriptions/1", 404)
    return menu


def check_order(base, menu, kitchen_password):
    order = {
        "customer": {
            "name": "Deploy check",
            "phone": "+55 11 90000-0000",
            "address": "Rua do Teste, 1",
        },
        "items": [{"pizza_id": menu[0]["id"], "quantity": 1}],
    }
    created = json.loads(expect_status("POST", f"{base}/api/orders", 201, body=order))
    order_id = created["id"]
    read = get_json(f"{base}/api/orders/{order_id}")
    if read["status"] != "received":
        raise CheckFailed(f"new order {order_id} has status {read['status']!r}, expected 'received'")
    print(f"ok  order {order_id} placed and read back")

    if not kitchen_password:
        print("--  KITCHEN_PASSWORD not set: kitchen board check skipped")
        return
    username = os.environ.get("KITCHEN_USERNAME") or "kitchen"
    login = base64.b64encode(f"{username}:{kitchen_password}".encode()).decode()
    auth = {"Authorization": f"Basic {login}"}
    expect_status("GET", f"{base}/kitchen/", 200, headers=auth)
    orders = get_json(f"{base}/kitchen/api/orders", headers=auth)
    if order_id not in {o["id"] for o in orders}:
        raise CheckFailed(f"order {order_id} is not on the kitchen board")
    expect_status(
        "PATCH", f"{base}/kitchen/api/orders/{order_id}/status", 200, body={"status": "preparing"}, headers=auth
    )
    print(f"ok  kitchen board lists order {order_id} and moved it to preparing")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("url", help="the environment's address, e.g. https://slicepizza.senatore.tech")
    parser.add_argument("version", help="the commit that must be live")
    parser.add_argument("--timeout", type=int, default=600, help="seconds to wait for the version (default 600)")
    parser.add_argument("--write", action="store_true", help="also place an order (staging only)")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    try:
        wait_for_version(base, args.version, args.timeout)
        menu = check_public(base)
        if args.write:
            check_order(base, menu, os.environ.get("KITCHEN_PASSWORD"))
    except CheckFailed as error:
        print(f"::error::{error}")
        return 1
    print(f"All checks passed on {base}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
