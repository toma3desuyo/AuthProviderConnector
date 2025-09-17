"""
SQLAlchemyデータベースモデル

ユーザーと連携アカウントのORMモデル定義
"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserModel(Base):
    """
    ユーザーテーブルモデル
    """
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    picture = Column(String(2048), nullable=True)

    # リレーション
    linked_accounts = relationship(
        "LinkedAccountModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class LinkedAccountModel(Base):
    """
    連携アカウントテーブルモデル
    """
    __tablename__ = 'linked_accounts'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey(
        'users.id'), nullable=False, index=True)
    provider_name = Column(String(100), nullable=False)
    provider_user_id = Column(String(255), nullable=False)

    # リレーション
    user = relationship("UserModel", back_populates="linked_accounts")
