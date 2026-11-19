# The "web" image: Caddy with the menu site and the kitchen board inside, in
# front of the API.
# Build it from the repository root (it needs frontend/ and infra/caddy/):
#
#   docker build -f infra/caddy/Dockerfile -t slicepizza-web .
#
# The root .dockerignore keeps everything else out of the build context.
# The version history for the pages, as JSON (releases.toml, ADR 0010): the
# kitchen's "What's new" and the version at the bottom of both pages. Made
# with the script the pipeline checks the file with, on the same Python as
# the API's image. Only /releases.json leaves this stage.
FROM python:3.15-slim AS releases
COPY releases.toml /src/releases.toml
COPY .github/scripts/releases.py /src/.github/scripts/releases.py
# The pipeline also passes the version it read (APP_VERSION): they must agree.
ARG APP_VERSION=unknown
RUN python3 -I /src/.github/scripts/releases.py --json > /releases.json \
    && found="$(python3 -I /src/.github/scripts/releases.py --version)" \
    && if [ "$APP_VERSION" != unknown ] && [ "$APP_VERSION" != "$found" ]; then \
         echo "APP_VERSION is $APP_VERSION but releases.toml says $found" >&2; exit 1; \
       fi

# A full version, so Dependabot proposes each update as a Pull Request
# (.github/dependabot.yml). The pipeline also rebuilds every week (ADR 0008),
# which picks up the Alpine fixes the official image gets under the same tag.
FROM caddy:2.11.9-alpine

# The official image gives the caddy binary the capability to bind ports below
# 1024. This image listens on 8080 and runs with all capabilities dropped and
# no-new-privileges, so remove it: a binary asking for a capability it cannot
# get may fail to start.
RUN setcap -r /usr/bin/caddy

COPY infra/caddy/Caddyfile /etc/caddy/Caddyfile
# Checks the kitchen login's settings, then starts Caddy (see the script).
COPY --chmod=755 infra/caddy/start.sh /usr/local/bin/start-web
COPY frontend/menu/ /srv/
# The kitchen board, served at /kitchen/ behind the kitchen login (ADR 0007).
COPY frontend/kitchen/ /srv-kitchen/
# /releases.json, outside /srv so docker-compose.site-dev.yml's folders don't hide it.
COPY --from=releases /releases.json /srv-data/releases.json

# Caddy writes nothing to disk with this Caddyfile, but point its folders to a
# place an unprivileged user can write, just in case.
ENV XDG_CONFIG_HOME=/tmp/caddy/config \
    XDG_DATA_HOME=/tmp/caddy/data

# The commit the image was built from, set by the pipeline (ADR 0008) and
# served at /version, so the deploy can check the new version is live.
ARG GIT_COMMIT=unknown
ENV GIT_COMMIT=$GIT_COMMIT

# Same unprivileged uid as the API image.
USER 10001:10001

EXPOSE 8080

CMD ["start-web"]
