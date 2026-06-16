"""Alembic 环境配置，使用项目 Settings 获取数据库连接"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 确保项目根目录在 sys.path 中
this_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(this_dir))  # MediaPilot/
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# this is the Alembic Config object
config = context.config

# 从环境变量读取 DATABASE_URL（通过 .env 文件）
if not config.get_main_option("sqlalchemy.url"):
    db_url = os.getenv("DATABASE_URL", "sqlite:///./mediapilot.db")
    config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 导入项目配置和模型
from backend.config.settings import settings  # noqa: E402
from backend.models.database.base import Base  # noqa: E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
