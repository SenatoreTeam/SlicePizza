# 0024: The kitchen logs in through the API, with a lockout and a session that expires

- **Status:** Accepted (to be built in [#98](https://github.com/SenatoreTeam/SlicePizza/issues/98); [ADR 0007](0007-kitchen-login.md) stays in force until that ships, then is marked "Superseded by 0024")
- **Date:** 2026-11-21
- **Phase:** 11 (task 11.7)

## Context

Today Caddy asks for the kitchen's password with HTTP Basic authentication ([ADR 0007](0007-kitchen-login.md)). It works, but:

- **Nothing stops guessing.** Caddy does not count wrong passwords. bcrypt makes each guess slow, which also means a flood of guesses costs the server a second of CPU each.
- **No session end.** The browser keeps the login until it is closed; a tablet by the oven is logged in for weeks, and there is no "log out".
- **One login, no room to grow.** Adding a second kitchen user or a log of who changed what needs a different mechanism anyway.

## Options considered

1. **Keep Basic authentication, limit wrong tries per IP in Caddy.** Small and invisible to the staff, but Caddy has no built-in lockout (a plugin or a log-watching tool would be needed), several IPs get around it, and the "no session end, no log out" problems stay.
2. **A login page in the kitchen, checked by the API** (this ADR). A form, a lockout after wrong passwords, a session cookie that expires.
3. **An external identity provider** (OAuth, an auth proxy). Rejected again for the reasons in ADR 0007: another service, and every kitchen device needs an account with it.

## Decision

Option 2.

```
browser ──/kitchen/ (page, no data in it) ───────────────────────────► Caddy: static files, public
browser ──POST /kitchen/api/login {password} ─► Caddy ─► API: checks password + lockout, sets the session cookie
browser ──/kitchen/api/orders + cookie ───────► Caddy ─► API: valid session? then the kitchen routes
scripts ──/api/orders + Bearer KITCHEN_API_TOKEN ───────► API: unchanged (CI, curl)
```

- **The password** lives on the **API** as a hash made with Python's standard `hashlib.scrypt` (no new dependency), created with a command (`python -m app.kitchen_login hash`). One shared kitchen login, as today; the user name is dropped. Caddy no longer asks for a password, and `KITCHEN_PASSWORD_HASH` moves from `web` to `api` in the new format: **a server step for Miguel** when it is released.
- **Lockout:** after **5 wrong passwords from one client address in 15 minutes**, that address gets `429` for **15 minutes**, without checking the password (so a flood costs no hashing). Counted per client address, never per account: locking the shared account would let anyone lock the real kitchen out during service. Counted in each API copy's memory, like the order rate limit ([ADR 0021](0021-hardening.md)); with N copies an attacker gets up to 5×N tries per window, acceptable for a long password.
- **Session:** a cookie signed by the API (HMAC with a key derived from `KITCHEN_API_TOKEN`, so there is no new secret), valid **12 hours**, `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/kitchen`. A **Log out** button clears it. Changing `KITCHEN_API_TOKEN` logs every device out.
- **Cross-site requests:** `SameSite=Strict` plus the API accepting only `application/json` bodies on the kitchen's write routes.
- **The token route stays** for scripts: `Authorization: Bearer <KITCHEN_API_TOKEN>` still works on the kitchen routes, so the CI tests and curl keep working. Caddy stops adding the token to browser calls.
- Every login, wrong password and lockout is logged with the client address and no password.

## Consequences

- **A password-guessing script is stopped** after 5 tries per address, and the board logs itself out after 12 hours.
- **The kitchen staff see a new login page** instead of the browser's pop-up, and must log in again every 12 hours. They need to be told before the release (a short pt-BR note).
- **Blocker before release: the API must see real client addresses.** The lockout uses the same address as the order rate limit (X-Forwarded-For through the server's proxy). If every request appears to come from the proxy, one wrong password streak would lock out everyone, the kitchen included. Miguel has been asked to check the `web` access log ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)); this must be confirmed before 11.7 is released.
- **Server step:** set the new `KITCHEN_PASSWORD_HASH` (scrypt) on `api`, remove the old one from `web`. Issue for Miguel at release time.
- **More code in the API** (login, sessions, lockout) and more tests; the Caddyfile gets simpler. Per-person accounts later become an extension of this, not a rewrite.
