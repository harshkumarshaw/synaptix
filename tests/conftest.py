"""
Synaptix Test Configuration — conftest.py

Shared pytest fixtures available across all test modules.
Fixtures here are automatically discovered by pytest.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment variables BEFORE any imports
os.environ.setdefault("SNX_ENV", "test")
os.environ.setdefault(
    "SNX_DATABASE_URL",
    "postgresql+asyncpg://snx_test:snx_test_pass@localhost:5436/synaptix_test",
)
os.environ.setdefault(
    "SNX_JWT_SECRET",
    "test_jwt_secret_that_is_long_enough_for_hs256_at_least_32_chars",
)

from packages.shared.db.base import Base

# ============================================================================
# Constants
# ============================================================================

JMN_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
JWT_SECRET = os.environ["SNX_JWT_SECRET"]


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio for all async tests."""
    return "asyncio"


@pytest.fixture
def tenant_id() -> uuid.UUID:
    """Return the JMN test tenant UUID."""
    return JMN_TENANT_ID


@pytest.fixture
def jwt_secret() -> str:
    """Return the test JWT secret."""
    return JWT_SECRET


@pytest.fixture
def test_user_id() -> uuid.UUID:
    """Return a test user UUID."""
    return TEST_USER_ID


@pytest.fixture(scope="session")
def app_settings() -> Any:
    """Return Settings singleton for testing."""
    from app.config import get_settings
    return get_settings()


@pytest_asyncio.fixture
async def db_session(tenant_id: uuid.UUID) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session scoped by tenant context."""
    import packages.shared.db.session as db_session_mod
    from sqlalchemy import text
    
    database_url = os.environ["SNX_DATABASE_URL"]
    if db_session_mod._engine is None:
        from sqlalchemy.pool import NullPool
        db_session_mod._engine = create_async_engine(
            database_url,
            poolclass=NullPool,
        )
        db_session_mod._async_session_factory = async_sessionmaker(
            bind=db_session_mod._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    
    async with db_session_mod._async_session_factory() as session:
        # Truncate tables to ensure a clean state for every test
        await session.execute(text("ALTER TABLE audit_log DISABLE TRIGGER trg_audit_log_no_update"))
        await session.execute(
            text(
                "TRUNCATE TABLE "
                "timetable_entries, timetable_slots, students, faculty, user_roles, "
                "workflow_transitions, workflow_instances, digital_assets, users, "
                "sections, batches, courses, departments, curricula, programs, "
                "academic_years, workflow_definitions, master_data_entities, audit_log "
                "CASCADE"
            )
        )
        await session.execute(text("ALTER TABLE audit_log ENABLE TRIGGER trg_audit_log_no_update"))
        await session.commit()

        await db_session_mod.set_tenant_context(session, tenant_id)
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_database_engine() -> AsyncGenerator[None, None]:
    yield
    import packages.shared.db.session as db_session_mod
    if db_session_mod._engine is not None:
        await db_session_mod._engine.dispose()

