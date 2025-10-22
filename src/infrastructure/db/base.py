"""SQLAlchemy Base定義"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# 命名規約を設定し、制約名・インデックス名の揺れを防ぐ
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """SQLAlchemyのベースクラス

    全てのORMモデルはこのクラスを継承する
    """

    # Alembicのautogenerateが決定的に動作するようメタデータを固定
    metadata = metadata
