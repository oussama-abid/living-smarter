# Text-mode assistant. Voice mode needs a microphone and speakers,
# so it runs outside Docker (uv sync --extra voice).
FROM python:3.13-slim

# uv, pinned to the version the lock file was made with
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first: this layer is cached until uv.lock changes
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .

# Run as an unprivileged user; the device database lives in a volume
RUN useradd --create-home assistant && mkdir /data && chown assistant /data
USER assistant
ENV DATABASE_PATH=/data/devices.db \
    PYTHONUNBUFFERED=1
VOLUME /data

CMD ["uv", "run", "--no-dev", "--no-sync", "python", "main.py"]
