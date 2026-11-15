#!/bin/sh
# Deploys one version to one environment (ADR 0009):
#
#   .github/scripts/deploy.sh <tag> <commit>      e.g. deploy.sh staging 0123abc...
#
# 1. Points the environment's tag (`staging`, or `latest` for production) at
#    the images built from <commit> (`sha-<commit>`), for api, web and worker.
#    The images are not rebuilt or downloaded: only the tag moves, so the
#    exact images tested on staging are the ones production gets.
# 2. Asks Dokploy to deploy, through the environment's deploy webhook
#    (DEPLOY_WEBHOOK_URL, a secret of the GitHub environment). Without it,
#    Dokploy's own auto-update picks up the moved tag within minutes.
#
# The caller then waits for the version with check_deploy.py. Needs a
# `docker login ghcr.io` with permission to push the packages.
set -eu

tag=$1
commit=$2
registry=ghcr.io/senatoreteam

case "$commit" in
	*[!0-9a-f]* | "") echo "::error::Not a commit: '$commit' (40 hexadecimal characters)." >&2; exit 1 ;;
esac
if [ "${#commit}" -ne 40 ]; then
	echo "::error::Not a full commit: '$commit' (40 hexadecimal characters)." >&2
	exit 1
fi

# Check all three exist before moving any tag, so a missing image can't leave
# the environment with a mix of versions.
for image in api web worker; do
	if ! docker buildx imagetools inspect "$registry/slicepizza-$image:sha-$commit" > /dev/null; then
		echo "::error::$registry/slicepizza-$image:sha-$commit does not exist. Only commits whose pipeline passed on main have images." >&2
		exit 1
	fi
done
for image in api web worker; do
	docker buildx imagetools create --tag "$registry/slicepizza-$image:$tag" "$registry/slicepizza-$image:sha-$commit"
	echo "$registry/slicepizza-$image:$tag -> sha-$commit"
done

if [ -z "${DEPLOY_WEBHOOK_URL:-}" ]; then
	echo "::warning::No DEPLOY_WEBHOOK_URL secret in this environment: waiting for Dokploy's auto-update to pick up :$tag instead (see docs/DEPLOY.md)."
	exit 0
fi
# The URL holds the webhook's token: never print it (GitHub masks secrets in
# the log, and curl's errors don't include the URL).
# Only 200 means a deploy was queued: Dokploy answers 301 when it decides not
# to deploy (a Git-based service on another branch), 400 when auto deploy is
# off for the service, and 404 for an unknown webhook.
answer=$(mktemp)
status=$(curl -sS --max-time 30 -X POST -H "Content-Type: application/json" -d '{}' \
	-o "$answer" -w '%{http_code}' "$DEPLOY_WEBHOOK_URL")
if [ "$status" != 200 ]; then
	echo "::error::Dokploy did not start a deploy (HTTP $status): $(head -c 300 "$answer")" >&2
	exit 1
fi
echo "Dokploy is deploying :$tag."
