"""Dependency injection container for AuthProviderConnector."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from config import Settings, settings
from authproviderconnector.context.users.infrastructure.factory import (
    UsersContext,
    UsersContextFactory,
)
from infrastructure.db.connection import Database

logger = logging.getLogger(__name__)


@dataclass
class Infrastructure:
    """Infrastructure dependencies."""

    database: Database


@dataclass
class Container:
    """Application-wide dependency container."""

    settings: Settings
    infrastructure: Infrastructure
    users_context: UsersContext


_container: Optional[Container] = None


def create_container(settings_override: Settings | None = None) -> Container:
    """Create a DI container instance."""
    global _container

    if _container is not None:
        return _container

    resolved_settings = settings_override or settings

    logger.info("Initializing dependency container")

    database = Database(resolved_settings.DATABASE_URL)
    users_context = UsersContextFactory.create(database)

    _container = Container(
        settings=resolved_settings,
        infrastructure=Infrastructure(database=database),
        users_context=users_context,
    )

    logger.info("Dependency container initialized")
    return _container


def get_container() -> Container:
    """Return the global container, creating it if necessary."""
    global _container
    if _container is None:
        _container = create_container()
    return _container


async def reset_container() -> None:
    """Dispose the current container (used in tests)."""
    global _container
    if _container is None:
        return

    await _container.infrastructure.database.close()
    _container = None
