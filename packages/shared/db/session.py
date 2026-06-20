"""
Synaptix Database Session Management.

Provides the async SQLAlchemy engine, session factory, and the critical
tenant context setter that enables Row Level Security (RLS).

CRITICAL: The tenant context MUST be set on every database session before
any queries run. This is enforced by the middleware, but every function
that creates a raw session must also set it.

Usage (FastAPI dependency):
    from packages.shared.db.session import get_db

    async def my_endpoint(db: Annotated[AsyncSession, Depends(get_db)]):
        ...
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from packages.shared.errors import TenantContextMissingError
from packages.shared.logging import get_logger

logger = get_logger(__name__)

# Module-level engine and session factory.
# Call configure_database() at application startup before any requests.
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def configure_database(
    database_url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
    echo: bool = False,
) -> None:
    """Configure the global database engine and session factory.

    Call this once at service startup (in app lifespan or on_startup).

    Args:
        database_url: Async SQLAlchemy URL (postgresql+asyncpg://...).
        pool_size: Connection pool size.
        max_overflow: Maximum overflow connections beyond pool_size.
        echo: If True, log all SQL (use only in DEBUG mode).
    """
    global _engine, _async_session_factory

    _engine = create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo,
        pool_pre_ping=True,  # detect stale connections
    )

    _async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,  # avoid lazy loading after commit
        autoflush=False,
        autocommit=False,
    )

    logger.info("Database configured", extra={"pool_size": pool_size})


async def set_tenant_context(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Set the PostgreSQL session variable for Row Level Security.

    This sets `snx.current_tenant_id` which the RLS policies on every
    tenant-scoped table check automatically.

    CRITICAL: This MUST be called before any query on a tenant-scoped table.
    The middleware calls this automatically for API requests.

    Args:
        session: The async database session.
        tenant_id: UUID of the current tenant.
    """
    await session.execute(
        text("SELECT set_config('snx.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )
    logger.debug(
        "Tenant context set",
        extra={"tenant_id": str(tenant_id)},
    )


@asynccontextmanager
async def get_session_with_tenant(
    tenant_id: uuid.UUID,
) -> AsyncGenerator[AsyncSession, None]:
    """Context manager that provides a session with tenant context pre-set.

    Use this for background jobs, celery tasks, or any non-request context
    that needs database access.

    Args:
        tenant_id: UUID of the tenant to scope all queries to.

    Yields:
        AsyncSession with RLS tenant context set.

    Example:
        async with get_session_with_tenant(tenant_id) as db:
            students = await db.execute(select(Student))
    """
    if _async_session_factory is None:
        raise RuntimeError(
            "Database not configured. Call configure_database() at startup."
        )

    async with _async_session_factory() as session:
        async with session.begin():
            await set_tenant_context(session, tenant_id)
            yield session


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a DB session with tenant context.

    The tenant_id is extracted from the request state (set by the tenant
    context middleware). If no tenant_id is present, raises TenantContextMissingError.

    This dependency is the STANDARD way to get a database session in endpoints.

    Args:
        request: FastAPI Request object (injected by FastAPI).

    Yields:
        AsyncSession with RLS tenant context set.

    Raises:
        TenantContextMissingError: If no tenant_id in request state.

    Example:
        async def my_endpoint(db: Annotated[AsyncSession, Depends(get_db)]):
            ...
    """
    if _async_session_factory is None:
        raise RuntimeError(
            "Database not configured. Call configure_database() at startup."
        )

    tenant_id: uuid.UUID | None = getattr(request.state, "tenant_id", None)

    if tenant_id is None:
        raise TenantContextMissingError(
            "Request arrived without a tenant context. "
            "Ensure the tenant middleware is applied and @require_tenant_context is used."
        )

    async with _async_session_factory() as session:
        async with session.begin():
            await set_tenant_context(session, tenant_id)
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
