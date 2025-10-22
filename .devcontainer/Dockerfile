FROM ghcr.io/astral-sh/uv:0.7.12 AS uv

FROM mcr.microsoft.com/devcontainers/python:dev-3.12-bookworm

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        vim \
        make \
        curl \
        build-essential \
        libpq-dev \
        pkg-config \
        unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/tmp/.uv-cache \
    VIRTUAL_ENV=/workspace/.venv
ENV PATH="/workspace/.venv/bin:$PATH"

RUN pip install --no-cache-dir uv

USER vscode
WORKDIR /workspace
