FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# requirements.txt is a lock file: exact versions and sha256 hashes (see
# "Dependencies" in README.md), installed the same way as the API's.
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements.txt

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
