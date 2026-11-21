FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# requirements.txt is a lock file: exact versions and sha256 hashes (see
# "Dependencies" in README.md), installed the same way as the API's.
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements.txt

# Hardening (Phase 8, ADR 0021). The image's own pip is not needed to run the
# app, and carries copies of libraries (urllib3, msgpack, setuptools) that
# vulnerability scans flag: remove it. zlib1g is upgraded when Debian has a
# security fix newer than the base image (a no-op once the base catches up).
RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && pip uninstall -y pip

COPY app ./app

# Run as an unprivileged user instead of root, like the API.
RUN useradd --create-home --uid 10001 worker
USER worker

# The commit the image was built from, set by the pipeline (ADR 0008) and
# logged at startup. Last, so a new commit doesn't invalidate the layers above.
ARG GIT_COMMIT=unknown
ENV GIT_COMMIT=$GIT_COMMIT
# The version (releases.toml, ADR 0010), set by the pipeline and logged too.
ARG APP_VERSION=unknown
ENV APP_VERSION=$APP_VERSION

# No port: the worker only makes outgoing connections (RabbitMQ, Telegram).
CMD ["python", "-m", "app.main"]
