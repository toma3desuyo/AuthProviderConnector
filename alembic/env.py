import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# プロジェクトのルート（src ディレクトリ）をパスに追加してアプリのモジュールを解決する
PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.append(str(PROJECT_SRC))

# Alembic が使用する設定オブジェクト
config = context.config

# logging 設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic の自動生成対象となるメタデータ
from models import Base  # noqa: E402

target_metadata = Base.metadata


def prevent_empty_migrations(context, revision, directives) -> None:
    """変更がない状態で空のマイグレーションが生成されるのを防ぐ。"""
    if not directives:
        return
    directive = directives[0]
    if hasattr(directive, "upgrade_ops") and directive.upgrade_ops.is_empty():
        raise ValueError(
            "No schema changes detected; refusing to create empty migration."
        )


# デフォルトは alembic.ini の設定を利用しつつ、環境変数で上書きできるようにする
DEFAULT_DATABASE_URL = config.get_main_option("sqlalchemy.url")
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        process_revision_directives=prevent_empty_migrations,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            process_revision_directives=prevent_empty_migrations,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
