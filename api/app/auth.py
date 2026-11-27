"""Checks for the routes that are not public (ADR 0006, ADR 0007, ADR 0024)."""

import hmac

from fastapi import Header, HTTPException, Request, status

from . import kitchen_login
from .config import settings


def bearer_matches(authorization: str | None, token: str) -> bool:
    """Whether an ``Authorization: Bearer <token>`` header carries ``token``."""
    scheme, _, given = (authorization or "").partition(" ")
    # compare_digest: the time taken does not reveal how much of it matched.
    return scheme.lower() == "bearer" and hmac.compare_digest(given.encode(), token.encode())


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_kitchen(
    request: Request,
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> None:
    """Only the kitchen may list orders and change their status.

    Two ways in: the kitchen board, logged in through /kitchen/api/session
    (a session cookie, checked in app/kitchen_login.py, ADR 0024), or a script
    with ``Authorization: Bearer <KITCHEN_API_TOKEN>`` (ADR 0007).
    """
    token = settings.kitchen_api_token
    if token is None:
        # A setup problem on the server, not the caller's fault.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kitchen access is not set up on this server (KITCHEN_API_TOKEN).",
        )
    if bearer_matches(authorization, token):
        return
    if kitchen_login.has_valid_session(request):
        if request.method not in ("GET", "HEAD"):
            kitchen_login.require_json(request)
        return
    raise unauthorized()
