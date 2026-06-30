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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

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
    """Use asyncio for all async tests (anyio backend)."""
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


@pytest.fixture
async def db_session(tenant_id: uuid.UUID) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session scoped by tenant context.

    Uses anyio-compatible plain @pytest.fixture (not @pytest_asyncio.fixture)
    so that both this fixture and the @pytest.mark.anyio test functions share
    the SAME event loop managed by the anyio pytest plugin. This avoids the
    infamous 'Future attached to a different loop' error that occurs when
    @pytest_asyncio.fixture and @pytest.mark.anyio run under separate loop
    managers on Linux.

    Creates a fresh NullPool engine per test to avoid asyncpg connection
    reuse across different event loops. NullPool closes connections
    immediately after each use — no pool state leaks between tests.
    """
    from sqlalchemy import text

    import packages.shared.db.session as db_session_mod

    database_url = os.environ["SNX_DATABASE_URL"]

    # Always fresh engine bound to the current event loop (anyio manages it).
    engine = create_async_engine(database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    # Expose on the shared module so service-level code finds it.
    db_session_mod._engine = engine
    db_session_mod._async_session_factory = session_factory

    async with session_factory() as session:
        # Truncate tables to ensure a clean state for every test
        await session.execute(text("ALTER TABLE audit_log DISABLE TRIGGER trg_audit_log_no_update"))
        await session.execute(
            text(
                "TRUNCATE TABLE "
                # Phase 2 tables (must come before Phase 1 tables they reference)
                "doap_session_records, logbook_assessments, logbook_entries, "
                "student_elective_preferences, elective_allocations, electives, "
                "attendance_accommodations, attendance_exemptions, attendance_summary, attendance, "
                "leave_requests, internship_rotations, "
                # Phase 1B logbook tables
                "aetcom_records, foundation_course_records, "
                # Phase 1B academic tables
                "sessions, lesson_plans, event_courses, event_faculty, events, "
                # Phase 1A academic tables
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

    # Dispose engine — closes all asyncpg connections for this test's loop.
    await engine.dispose()
    db_session_mod._engine = None
    db_session_mod._async_session_factory = None


@pytest.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Real SQLite in-memory database for integration-style unit/workflow tests."""
    from packages.shared.db.base import Base
    
    # Import logbook & elective models so they register with Base.metadata
    import app.models.electives
    import app.models.logbook
    import app.models.logbook_phase2
    import app.models.stubs

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

    await engine.dispose()

