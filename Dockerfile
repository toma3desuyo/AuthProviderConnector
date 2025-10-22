FROM python:3.12-slim-bookworm

SHELL ["/bin/bash", "-euo", "pipefail", "-c"]

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    git \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app \
    && mkdir -p /home/appuser \
    && chown -R appuser:appuser /home/appuser

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path --default-toolchain stable \
    && chmod -R a+w "$RUSTUP_HOME" "$CARGO_HOME" \
    && chown -R appuser:appuser "$RUSTUP_HOME" "$CARGO_HOME"

COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    UV_REQUEST_TIMEOUT=600 \
    UV_CONCURRENT_DOWNLOADS=4 \
    UV_FROZEN=1 \
    UV_CACHE_DIR=/tmp/.uv-cache \
    PYTHONUNBUFFERED=1

USER appuser

COPY --chown=appuser:appuser . .

RUN uv sync --no-dev --no-editable

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/src

CMD ["uv", "run", "up"]
