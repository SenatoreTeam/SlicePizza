# Keep the version in api/.python-version: the lock files are resolved for it,
# and CI fails if the two differ.
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# requirements.txt is a lock file: exact versions and sha256 hashes (see
# "Dependencies" in README.md). --require-hashes refuses any file whose hash is
# not in it; --only-binary refuses to compile anything from source, because the
# tools pip would download for that are not hash-checked.
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements.txt

# Hardening (Phase 8, ADR 0021). The image's own pip is not needed to run the
# app, and carries copies of libraries (urllib3, msgpack, setuptools) that
# vulnerability scans flag: remove it. zlib1g and libzstd1 (CVE-2026-124851) are
# upgraded when Debian has a security fix newer than the base image (a no-op
# once the base catches up).
RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade zlib1g libzstd1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip uninstall -y pip

COPY app ./app

# Run as an unprivileged user instead of root.
RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8000

# The commit the image was built from, set by the pipeline (ADR 0008).
# /health reports it, so the deploy can check the new version is the one
# answering. Last, so a new commit doesn't invalidate the layers above.
ARG GIT_COMMIT=unknown
ENV GIT_COMMIT=$GIT_COMMIT
# The version (releases.toml, ADR 0010), set by the pipeline: /health and the
# docs at /api/docs say it.
ARG APP_VERSION=unknown
ENV APP_VERSION=$APP_VERSION

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
