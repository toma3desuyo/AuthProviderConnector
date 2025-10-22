"""Asynchronous database connection management."""

from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from infrastructure.db.base import Base


class Database:
    """Manage asynchronous database connections."""

    def __init__(self, database_url: str) -> None:
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://"
            )

        self._database_url = database_url
        self._engine: AsyncEngine | None = None
        self._async_session_maker: async_sessionmaker[AsyncSession] | None = None

        is_test_env = "PYTEST_XDIST_WORKER" in os.environ or "pytest" in sys.modules
        is_parallel_env = (
            is_test_env or os.environ.get("PARALLEL_WORKERS", "false").lower() == "true"
        )

        self._pool_size = int(
            os.environ.get("DB_POOL_SIZE", "3" if is_parallel_env else "5")
        )
        self._max_overflow = int(
            os.environ.get("DB_MAX_OVERFLOW", "5" if is_parallel_env else "10")
        )
        self._pool_timeout = int(
            os.environ.get("DB_POOL_TIMEOUT", "60" if is_parallel_env else "30")
        )
        self._pool_recycle = int(
            os.environ.get("DB_POOL_RECYCLE", "300" if is_parallel_env else "3600")
        )
        self._connection_timeout = int(
            os.environ.get("DB_CONNECTION_TIMEOUT", "60" if is_parallel_env else "5")
        )

    def _ensure_engine(self) -> None:
        if self._engine is None:
            is_test_env = (
                "PYTEST_XDIST_WORKER" in os.environ
                or "pytest" in sys.modules
                or os.environ.get("ENVIRONMENT") == "test"
            )

            if (
                is_test_env
                and os.environ.get("DB_USE_NULL_POOL", "false").lower() == "true"
            ) or (
                "pytest" in sys.modules
                and os.environ.get("DB_USE_NULL_POOL", "false").lower() == "true"
            ):
                self._engine = create_async_engine(
                    self._database_url,
                    echo=os.environ.get("DB_ECHO", "false").lower() == "true",
                    poolclass=NullPool,
                    connect_args={
                        "server_settings": {
                            "jit": "off",
                            "statement_timeout": f"{self._connection_timeout * 1000}ms",
                        },
                        "timeout": self._connection_timeout,
                        "command_timeout": self._connection_timeout,
                        "prepared_statement_cache_size": 0,
                        "prepared_statement_name_func": lambda: None,
                    },
                )
            else:
                self._engine = create_async_engine(
                    self._database_url,
                    echo=os.environ.get("DB_ECHO", "false").lower() == "true",
                    pool_pre_ping=os.environ.get("DB_POOL_PRE_PING", "false").lower()
                    == "true",
                    pool_size=self._pool_size,
                    max_overflow=self._max_overflow,
                    pool_timeout=self._pool_timeout,
                    pool_recycle=self._pool_recycle,
                    connect_args={
                        "server_settings": {
                            "jit": "off",
                            "statement_timeout": f"{self._connection_timeout * 1000}ms",
                        },
                        "timeout": self._connection_timeout,
                        "command_timeout": self._connection_timeout,
                        "prepared_statement_cache_size": int(
                            os.environ.get("DB_PREPARED_STATEMENT_CACHE_SIZE", "0")
                        ),
                        "prepared_statement_name_func": lambda: None
                        if is_test_env
                        else None,
                    },
                )
            self._async_session_maker = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

    @property
    def engine(self) -> AsyncEngine:
        self._ensure_engine()
        assert self._engine is not None
        return self._engine

    @property
    def async_session_maker(self) -> async_sessionmaker[AsyncSession]:
        self._ensure_engine()
        assert self._async_session_maker is not None
        return self._async_session_maker

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        if self._engine is None:
            return

        try:
            await self._engine.dispose()
            await asyncio.sleep(0.1)
        except Exception as exc:  # pragma: no cover - best effort cleanup
            print(f"Warning: Exception during database close: {exc}")

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self.async_session_maker
