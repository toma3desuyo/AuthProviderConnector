"""
SQLAlchemyデータベースモデル

ユーザーと連携アカウントのORMモデル定義
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.db.base import Base


class UserModel(Base):
    """
    ユーザーテーブルモデル
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    picture: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # リレーション
    linked_accounts: Mapped[list[LinkedAccountModel]] = relationship(
        "LinkedAccountModel", back_populates="user", cascade="all, delete-orphan"
    )


class LinkedAccountModel(Base):
    """
    連携アカウントテーブルモデル
    """

    __tablename__ = "linked_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # リレーション
    user: Mapped[UserModel] = relationship(
        "UserModel", back_populates="linked_accounts"
    )
