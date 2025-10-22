#!/bin/bash
set -euo pipefail

if [ -f .devcontainer/scripts/register-aliases.sh ]; then
  bash .devcontainer/scripts/register-aliases.sh
fi

cd /workspace
uv sync --no-dev
