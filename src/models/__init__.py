"""Aggregate SQLAlchemy models for Alembic autogeneration."""

from infrastructure.db.base import Base
from authproviderconnector.context.users.infrastructure.model import (
    LinkedAccountModel,
    UserModel,
)

__all__ = ["Base", "UserModel", "LinkedAccountModel"]
