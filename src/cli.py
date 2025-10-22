"""Command line entry point for running the API service."""

from __future__ import annotations

import logging

import uvicorn

from config import settings
from main import app

logger = logging.getLogger(__name__)


def run() -> None:
    """Launch the FastAPI application under Uvicorn."""
    reload_enabled = settings.ENVIRONMENT == "development"
    logger.info(
        "Starting AuthProviderConnector (reload=%s, host=%s, port=%s)",
        reload_enabled,
        "0.0.0.0",
        8000,
    )
    uvicorn_target = "main:app" if reload_enabled else app
    uvicorn.run(
        uvicorn_target,
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled,
        reload_dirs=["/app/src"] if reload_enabled else None,
        log_level="info",
    )
