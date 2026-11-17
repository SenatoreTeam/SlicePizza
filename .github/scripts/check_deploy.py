"""Wait until production runs a new version, then check it like a visitor (ADR 0011).

Used by the pipeline's "production check", after its release job published a
new version (ADR 0009). The server installs the version by itself; GitHub never
reaches the server, so this only looks at the public site:

    python3 -I .github/scripts/check_deploy.py https://slicepizza.senatore.tech <commit> --release 1.2.0

1. Waits (up to --timeout seconds) until the web container's /version and the
   API's /api/health both report <commit>, and, with --release, until
   /api/health's "release" and /releases.json's "version" say that version:
   the server looks for new versions every 2 minutes, so the old one answers
   for a while.
2. Checks what any visitor sees: the menu site, the menu, the API docs, and
   that the private routes stay private (/kitchen asks for a login, listing or
   changing orders without the kitchen's token is refused, /api/internal is
   not reachable).

It never writes: placing an order would reach the real kitchen and the
pizzeria's Telegram. Exit code 0 when everything passed, 1 otherwise. Standard
library only: it runs on the runner's python3 without installing anything.
"""

import argparse
import json
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
    """What /version, /api/health and /releases.json report right now (None if unreachable).

    Returns (web commit, API commit, API release, web release).
    """
    web = api = api_release = web_release = None
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
                api_release = health.get("release")
        else:
            api = f"<HTTP {status}>"
    except (OSError, ValueError):
        pass
    try:
        # The version history the web image was built with (releases.toml, ADR 0010).
        status, text = request("GET", f"{base}/releases.json", timeout=10)
        if status == 200:
            web_release = json.loads(text).get("version")
    except (OSError, ValueError, AttributeError):
        pass
    return web, api, api_release, web_release


def wait_for_version(base, commit, release, timeout):
    deadline = time.monotonic() + timeout
    wanted = (commit, commit, release, release) if release else (commit, commit)
    last = None
    while True:
        current = live_versions(base)
        if current != last:
            print(f"live: web={current[0]} api={current[1]} release: api={current[2]} web={current[3]}")
            last = current
        if current[: len(wanted)] == wanted:
            print(f"ok  {base} runs {release + ' = ' if release else ''}{commit}")
            return
        if time.monotonic() > deadline:
            raise CheckFailed(
                f"{base} still reports web={current[0]} api={current[1]} (release {current[2]}) after "
                f"{timeout} s, not {release or ''} {commit}. The server installs a new version within a few "
                "minutes, and puts the previous one back if its own checks fail: ask the server's "
                "administrator, or see the SlicePizza dashboard."
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


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("url", help="the site's address, e.g. https://slicepizza.senatore.tech")
    parser.add_argument("commit", help="the commit that must be live")
    parser.add_argument("--release", help="the version that must be live, e.g. 1.2.0 (releases.toml)")
    parser.add_argument("--timeout", type=int, default=900, help="seconds to wait for the version (default 900)")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    try:
        wait_for_version(base, args.commit, args.release, args.timeout)
        check_public(base)
    except CheckFailed as error:
        print(f"::error::{error}")
        return 1
    print(f"All checks passed on {base}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
