# 0024: The kitchen logs in through the API, with a lockout and a session that expires

- **Status:** Accepted, built in [#98](https://github.com/SenatoreTeam/SlicePizza/issues/98). Supersedes [ADR 0007](0007-kitchen-login.md)'s login (its token stays)
- **Date:** 2026-11-21, revised 2026-11-26 before building (see "Revision" at the end)
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
browser ──POST /kitchen/api/session {password} ► Caddy ─► API: checks password + lockout, sets the session cookie
browser ──/kitchen/api/orders + cookie ───────► Caddy ─► API: valid session? then the kitchen routes
scripts ──/api/orders + Bearer KITCHEN_API_TOKEN ───────► API: unchanged (CI, curl)
```

- **The password** stays as today's bcrypt hash in `KITCHEN_PASSWORD_HASH` on `web` (`caddy hash-password`). Caddy no longer asks for it; on the kitchen's route it passes the hash to the API in `X-Kitchen-Password-Hash`, and the API checks the password with the `bcrypt` library. One shared kitchen login, as today; the user name is dropped. **No change on the server.**
- **Only through the kitchen's route:** Caddy also sends `X-Kitchen-Proxy: <KITCHEN_API_TOKEN>` on `/kitchen/api/*`, and removes both headers on the public `/api/*`. Without a matching token the login answers 404 and a session cookie is ignored, so a forged hash header is useless.
- **Lockout:** after **5 wrong passwords from one client address in 15 minutes**, that address gets `429` for **15 minutes**, without checking the password (so a flood costs no hashing). Counted per client address, never per account: locking the shared account would let anyone lock the real kitchen out during service. Counted in each API copy's memory, like the order rate limit ([ADR 0021](0021-hardening.md)); with N copies an attacker gets up to 5×N tries per window, acceptable for a long password.
- **The client address** is worked out by Caddy and passed to the API as a single `X-Forwarded-For` value. Caddy now trusts `100.64.0.0/10` by default (the live server's Traefik is at `100.80.1.0/24`) and reads the header strictly from the right, so a customer can't choose their address by sending one.
- **Session:** a cookie signed by the API (HMAC with a key derived from `KITCHEN_API_TOKEN`, so there is no new secret; the signature covers the expiry and the password hash), valid **12 hours**, `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/kitchen`. A **Log out** button clears it. Changing the password or `KITCHEN_API_TOKEN` logs every device out.
- **Cross-site requests:** `SameSite=Strict` plus the API accepting only `application/json` bodies on the login and on the kitchen's writes (415 otherwise).
- **The token route stays** for scripts: `Authorization: Bearer <KITCHEN_API_TOKEN>` still works on the kitchen routes, so the CI tests and curl keep working. Caddy stops adding it to browser calls.
- Every login, wrong password and lockout is logged with the client address and no password.

## Consequences

- **A password-guessing script is stopped** after 5 tries per address, and the board logs itself out after 12 hours.
- **The kitchen staff see a new login page** instead of the browser's pop-up, and must log in again every 12 hours. They need to be told before the release (a short pt-BR note).
- **Real client addresses, without the server's help.** Tested in Docker with a copy of the server's chain (a proxy at `100.80.1.10` in front of `web`): before this change, with the server's settings as documented, every customer looked like the proxy's address, so one person's wrong passwords locked everyone out (and the order rate limit counted everyone together). With Caddy's new defaults each customer has their own address, whether or not the server sets `TRUSTED_PROXIES`, and a forged `X-Forwarded-For` is ignored. If the addresses were ever wrong again, the lockout only gets stricter (a stranger could lock the kitchen out for 15 minutes), never weaker.
- **No server step:** the same `KITCHEN_PASSWORD_HASH` and `KITCHEN_API_TOKEN` as today.
- **More code in the API** (login, sessions, lockout) and more tests; the Caddyfile gets simpler. Per-person accounts later become an extension of this, not a rewrite.

## Revision (2026-11-26, before building)

The first version of this ADR moved the password to the API as a new scrypt hash (Python's standard library, no new dependency). That needed the server's owner to set a new variable before release, and the release would wait on it. Keeping the bcrypt hash on `web` and passing it to the API on the kitchen's route needs nothing on the server, at the cost of one dependency (`bcrypt`, wheels for every Python, pinned with hashes). The client-address fix in Caddy came out of the Docker test.
