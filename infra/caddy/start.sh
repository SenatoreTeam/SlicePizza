#!/bin/sh
# Starts Caddy in the web image.
#
# First it checks the kitchen login's settings (ADR 0007). Caddy refuses to
# start at all with a malformed or empty hash or user name, which would take
# the whole site down with the kitchen. So a malformed value only turns the kitchen login off (/kitchen
# answers 404), with an error in the log saying why; the menu site and the
# API keep working.
#
# Accepted: a bcrypt hash from `caddy hash-password`, either as it is
# ($2a$14$...) or base64-encoded (what docs/DEPLOY.md recommends). A trailing
# newline is ignored.
# The single-quoted $2 below is the literal start of a bcrypt hash, not a
# variable: SC2016 ("expressions don't expand in single quotes") is expected.
# shellcheck disable=SC2016
set -eu

hash="${KITCHEN_PASSWORD_HASH:-}"
if [ -n "$hash" ]; then
	case "$hash" in
		'$2'*) raw="$hash" ;;
		*) raw="$(printf '%s' "$hash" | base64 -d 2>/dev/null || true)" ;;
	esac
	raw="$(printf '%s' "$raw" | tr -d '\r\n')"
	if ! printf '%s' "$raw" | grep -Eq '^\$2[aby]?\$[0-9]{2}\$[./A-Za-z0-9]{53}$'; then
		echo "ERROR: KITCHEN_PASSWORD_HASH is not a bcrypt hash from 'caddy hash-password' (plain or base64-encoded)." >&2
		echo "ERROR: The kitchen login is OFF (/kitchen answers 404) until it is fixed; the rest of the site runs normally. See docs/DEPLOY.md, section Kitchen." >&2
		hash=""
	fi
fi
# Empty must mean "not set": Caddy only falls back to its defaults for unset
# variables, and an empty user name or hash stops it from starting.
if [ -z "$hash" ]; then
	unset KITCHEN_PASSWORD_HASH
fi
if [ -z "${KITCHEN_USERNAME:-}" ]; then
	unset KITCHEN_USERNAME
fi
# The API's address. API_UPSTREAM (host:port) is the old setting, still honoured
# so a server that has it keeps working; API_HOST and API_PORT are the new ones
# (the Caddyfile needs them apart to find every API copy, ADR 0020).
if [ -n "${API_UPSTREAM:-}" ]; then
	API_HOST="${API_UPSTREAM%:*}"
	API_PORT="${API_UPSTREAM##*:}"
	export API_HOST API_PORT
fi
if [ -z "${TRUSTED_PROXIES:-}" ]; then
	unset TRUSTED_PROXIES
fi

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
