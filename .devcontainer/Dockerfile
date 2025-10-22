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

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g npm@11.4.2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN NPM_PREFIX=$(npm config get prefix) \
    && mkdir -p "$NPM_PREFIX/lib/node_modules" \
    && chown -R vscode:vscode "$NPM_PREFIX/lib/node_modules"

COPY --from=uv /uv /uvx /bin/

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/tmp/.uv-cache \
    VIRTUAL_ENV=/authproviderconnector/.venv
ENV PATH="/authproviderconnector/.venv/bin:$PATH"

RUN pip install --no-cache-dir uv

USER vscode
WORKDIR /authproviderconnector

ENV NPM_CONFIG_PREFIX=/home/vscode/.npm-global
ENV PATH=$NPM_CONFIG_PREFIX/bin:$PATH

RUN mkdir -p $NPM_CONFIG_PREFIX \
    && npm config set prefix "$NPM_CONFIG_PREFIX" \
    && echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
