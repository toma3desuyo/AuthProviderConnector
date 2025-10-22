"""FastAPI application entry point for AuthProviderConnector."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from authproviderconnector.context.users.presentation.router import (
    create_auth_router,
)
from config import settings
from infrastructure.di import Container, create_container, get_container

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s - %(name)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application startup and shutdown."""
    container: Container = get_container()
    app.state.container = container

    logger.info("AuthProviderConnector starting up...")
    try:
        yield
    finally:
        logger.info("AuthProviderConnector shutting down...")
        await container.infrastructure.database.close()
        logger.info("AuthProviderConnector shut down successfully")


def create_app() -> FastAPI:
    """Create a FastAPI application instance."""
    app = FastAPI(
        title="AuthProviderConnector API",
        version="1.0.0",
        description="Auth0 based authentication connector",
        lifespan=lifespan,
    )

    app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)

    container = create_container()
    app.state.container = container

    auth_router = create_auth_router(container.users_context)
    app.include_router(auth_router)

    @app.get("/api/v1/health", tags=["system"])
    async def healthcheck() -> JSONResponse:
        """Return basic health information."""
        db_status = "ok"
        try:
            async with container.infrastructure.database.get_session() as session:
                await session.execute(text("SELECT 1"))
        except Exception as exc:  # pragma: no cover - health guard
            logger.exception("Database health check failed", exc_info=exc)
            db_status = "error"
        return JSONResponse({"status": "ok", "database": db_status})

    return app


app = create_app()
