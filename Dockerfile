FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .

RUN useradd --create-home assistant && mkdir /data && chown assistant /data
USER assistant
ENV DATABASE_PATH=/data/devices.db \
    PYTHONUNBUFFERED=1
VOLUME /data

CMD ["uv", "run", "--no-dev", "--no-sync", "python", "main.py"]
