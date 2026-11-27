"""The kitchen's login: a password, a lockout and a session that expires (ADR 0024).

The kitchen board at /kitchen/ is a public page with no data in it. Its calls go
to /kitchen/api/..., which Caddy forwards here with two headers that only the
web container can add:

- ``X-Kitchen-Proxy: <KITCHEN_API_TOKEN>``: the request came through the
  kitchen's route. Without it, the login routes answer 404 and a session cookie
  is ignored, so nothing here works through the public /api.
- ``X-Kitchen-Password-Hash``: the bcrypt hash in the web container's
  ``KITCHEN_PASSWORD_HASH`` (``caddy hash-password``, plain or base64). The hash
  stays where it always was, so this login needs no change on the server.

``POST /session {"password": ...}`` checks the password and sets a cookie
signed by the API, valid for ``SESSION_HOURS``. ``DELETE /session`` logs out.
The signature covers the expiry and the password hash, so changing the password
(or ``KITCHEN_API_TOKEN``) logs every device out.

Lockout: ``MAX_FAILURES`` wrong passwords from one client address within
``LOCK_SECONDS`` lock that address for ``LOCK_SECONDS``; while locked, the
password is not even checked, so a flood costs no bcrypt work. It counts per
address, never per account: locking the one shared account would let anyone
lock the real kitchen out during service. If the proxies in front made every
client look like one address, the lockout would only get stricter (an attacker
could then lock the kitchen out for 15 minutes), never weaker. The counters
live in this process, like the order rate limit (ADR 0021).

Scripts keep using ``Authorization: Bearer <KITCHEN_API_TOKEN>`` (app/auth.py).
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import logging
import re
import threading
import time
from collections import deque
from datetime import UTC, datetime

import bcrypt
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from .config import settings

logger = logging.getLogger(__name__)

PROXY_HEADER = "X-Kitchen-Proxy"
HASH_HEADER = "X-Kitchen-Password-Hash"
COOKIE = "kitchen_session"
COOKIE_PATH = "/kitchen"
SESSION_HOURS = 12
MAX_FAILURES = 5
LOCK_SECONDS = 15 * 60
MAX_CLIENTS = 10_000  # bound on remembered addresses

_BCRYPT = re.compile(r"^\$2[aby]?\$[0-9]{2}\$[./A-Za-z0-9]{53}$")


# --- Where the request came from ---------------------------------------------------


def from_kitchen_route(request: Request) -> bool:
    """True when Caddy's /kitchen/api route forwarded the request (it adds the token)."""
    token = settings.kitchen_api_token
    given = request.headers.get(PROXY_HEADER, "")
    return bool(token) and hmac.compare_digest(given.encode(), token.encode())


def password_hash(request: Request) -> bytes | None:
    """The kitchen password's bcrypt hash Caddy forwarded, or None if missing or malformed."""
    value = request.headers.get(HASH_HEADER, "").strip()
    if not value.startswith("$2"):
        try:
            value = base64.b64decode(value, validate=True).decode().strip()
        except (binascii.Error, UnicodeDecodeError):
            return None
    return value.encode() if _BCRYPT.match(value) else None


def client_address(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# --- Session cookie -------------------------------------------------------------------


def _signature(expires: int, hashed: bytes) -> str:
    token = settings.kitchen_api_token or ""
    key = hmac.new(token.encode(), b"slicepizza kitchen session", hashlib.sha256).digest()
    message = f"{expires}.{hashlib.sha256(hashed).hexdigest()}".encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def new_session(hashed: bytes, now: float | None = None) -> tuple[str, int]:
    expires = int(now if now is not None else time.time()) + SESSION_HOURS * 3600
    return f"{expires}.{_signature(expires, hashed)}", expires


def session_is_valid(cookie: str | None, hashed: bytes, now: float | None = None) -> bool:
    expires_text, _, signature = (cookie or "").partition(".")
    if not expires_text.isdigit() or not signature:
        return False
    expires = int(expires_text)
    if expires <= (now if now is not None else time.time()):
        return False
    return hmac.compare_digest(signature.encode(), _signature(expires, hashed).encode())


def has_valid_session(request: Request) -> bool:
    """A browser on the kitchen board, logged in (used by app/auth.py)."""
    if not from_kitchen_route(request):
        return False
    hashed = password_hash(request)
    return hashed is not None and session_is_valid(request.cookies.get(COOKIE), hashed)


# --- Lockout ----------------------------------------------------------------------------


class LoginGuard:
    """Counts wrong passwords per client address and locks an address that has too many."""

    def __init__(self, max_failures: int = MAX_FAILURES, lock_seconds: float = LOCK_SECONDS) -> None:
        self.max_failures = max_failures
        self.lock_seconds = lock_seconds
        self._failures: dict[str, deque[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, client: str, now: float | None = None) -> float:
        """Seconds until ``client`` may try again; 0 if it may try now."""
        now = time.monotonic() if now is None else now
        with self._lock:
            until = self._locked_until.get(client, 0.0)
            if until > now:
                return until - now
            self._locked_until.pop(client, None)
            return 0.0

    def failed(self, client: str, now: float | None = None) -> bool:
        """Record a wrong password. True if this one locked the address."""
        now = time.monotonic() if now is None else now
        with self._lock:
            failures = self._failures.setdefault(client, deque())
            while failures and failures[0] <= now - self.lock_seconds:
                failures.popleft()
            failures.append(now)
            if len(failures) >= self.max_failures:
                self._locked_until[client] = now + self.lock_seconds
                failures.clear()
                return True
            if len(self._failures) > MAX_CLIENTS:
                self._purge(now)
            return False

    def succeeded(self, client: str) -> None:
        with self._lock:
            self._failures.pop(client, None)

    def _purge(self, now: float) -> None:
        for key in [k for k, f in self._failures.items() if not f or f[-1] <= now - self.lock_seconds]:
            del self._failures[key]
        for key in [k for k, until in self._locked_until.items() if until <= now]:
            del self._locked_until[key]

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()
            self._locked_until.clear()


guard = LoginGuard()


# --- Routes ----------------------------------------------------------------------------

router = APIRouter(include_in_schema=False)


class LoginIn(BaseModel):
    password: str = Field(min_length=1, max_length=200)


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")


def _too_many(wait: float) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many wrong passwords. Try again in 15 minutes.",
        headers={"Retry-After": str(int(wait) + 1)},
    )


def require_json(request: Request) -> None:
    # A form posted from another site sends form-encoded data; only our page sends JSON.
    if not request.headers.get("content-type", "").startswith("application/json"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Send JSON.")


@router.post("/session")
def log_in(payload: LoginIn, request: Request, response: Response) -> dict[str, str]:
    """Log the kitchen board in (only through Caddy's /kitchen/api route)."""
    if not from_kitchen_route(request):
        raise _not_found()
    require_json(request)
    hashed = password_hash(request)
    if hashed is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The kitchen login is not set up on this server (KITCHEN_PASSWORD_HASH).",
        )
    client = client_address(request)
    wait = guard.wait(client)
    if wait:
        logger.warning("Kitchen login refused for %s: locked for %.0f more seconds", client, wait)
        raise _too_many(wait)
    # bcrypt takes about a second on purpose; FastAPI runs this in a worker thread.
    if not bcrypt.checkpw(payload.password.encode(), hashed):
        if guard.failed(client):
            logger.warning(
                "Kitchen login: %d wrong passwords from %s, locked for %d minutes",
                MAX_FAILURES,
                client,
                LOCK_SECONDS // 60,
            )
            raise _too_many(LOCK_SECONDS)
        logger.warning("Kitchen login: wrong password from %s", client)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password.")
    guard.succeeded(client)
    value, expires = new_session(hashed)
    response.set_cookie(
        COOKIE,
        value,
        max_age=SESSION_HOURS * 3600,
        path=COOKIE_PATH,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    logger.info("Kitchen login from %s", client)
    return {"expires_at": datetime.fromtimestamp(expires, UTC).isoformat()}


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
def log_out(request: Request, response: Response) -> None:
    """Forget this browser's session."""
    if not from_kitchen_route(request):
        raise _not_found()
    response.delete_cookie(COOKIE, path=COOKIE_PATH, secure=True, httponly=True, samesite="strict")
