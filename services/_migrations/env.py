"""
Alembic Environment Configuration for Synaptix.

Single migration chain for the entire monorepo (ADR-004).
Configured for async SQLAlchemy (asyncpg driver).

All service models are imported here so Alembic can detect schema changes.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Import all models so Alembic can detect them
# Add new service models here as they are created
from packages.shared.db.base import Base  # noqa: F401

# Service models — uncomment as services are built
# from services.snx-auth.app.models.user import User, Tenant, Role  # noqa: F401

# Alembic Config object
config = context.config

# Override sqlalchemy.url with environment variable if set
database_url = os.environ.get("SNX_DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection needed)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async connection)."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url", ""),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(
                connection=conn,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
            )
        )
        await connection.run_sync(lambda conn: context.run_migrations())

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
