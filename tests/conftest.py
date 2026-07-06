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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import NullPool


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
                "admission_applications, doap_session_records, logbook_assessments, logbook_entries, "
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
    """Real PostgreSQL database for integration-style unit/workflow tests."""
    from sqlalchemy import text

    import packages.shared.db.session as db_session_mod

    database_url = os.environ.get("SNX_DATABASE_URL")
    if not database_url:
        database_url = "postgresql+asyncpg://snx_test:snx_test_pass@localhost:5436/synaptix_test"

    engine = create_async_engine(database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    db_session_mod._engine = engine
    db_session_mod._async_session_factory = session_factory

    async with session_factory() as session:
        # List of tables
        tables = [
            "admission_applications",
            "doap_session_records",
            "logbook_assessments",
            "logbook_entries",
            "student_elective_preferences",
            "elective_allocations",
            "electives",
            "attendance_accommodations",
            "attendance_exemptions",
            "attendance_summary",
            "attendance",
            "leave_requests",
            "internship_rotations",
            "aetcom_records",
            "foundation_course_records",
            "sessions",
            "lesson_plans",
            "event_courses",
            "event_faculty",
            "events",
            "timetable_entries",
            "timetable_slots",
            "students",
            "faculty",
            "user_roles",
            "workflow_transitions",
            "workflow_instances",
            "digital_assets",
            "users",
            "sections",
            "batches",
            "courses",
            "departments",
            "curricula",
            "programs",
            "academic_years",
            "workflow_definitions",
            "master_data_entities",
            "audit_log",
            "mdm_configs",
        ]

        # Truncate tables to ensure a clean state for every test
        await session.execute(text("ALTER TABLE audit_log DISABLE TRIGGER trg_audit_log_no_update"))
        await session.execute(
            text(
                "TRUNCATE TABLE "
                "admission_applications, doap_session_records, logbook_assessments, logbook_entries, "
                "student_elective_preferences, elective_allocations, electives, "
                "attendance_accommodations, attendance_exemptions, attendance_summary, attendance, "
                "leave_requests, internship_rotations, "
                "aetcom_records, foundation_course_records, "
                "sessions, lesson_plans, event_courses, event_faculty, events, "
                "timetable_entries, timetable_slots, students, faculty, user_roles, "
                "workflow_transitions, workflow_instances, digital_assets, users, "
                "sections, batches, courses, departments, curricula, programs, "
                "academic_years, workflow_definitions, master_data_entities, audit_log, mdm_configs "
                "CASCADE"
            )
        )
        await session.execute(text("ALTER TABLE audit_log ENABLE TRIGGER trg_audit_log_no_update"))
        await session.commit()

        # Disable all triggers (including FK constraints) on all tables for the duration of the test
        for table in tables:
            await session.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER ALL"))
        await session.commit()

        yield session

        # Re-enable triggers at the end of the test
        for table in tables:
            await session.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER ALL"))
        await session.commit()

    await engine.dispose()
    db_session_mod._engine = None
    db_session_mod._async_session_factory = None


@pytest.fixture
def seed_deps() -> Any:
    """Fixture returning a helper function to seed basic FK relationships."""

    async def _seed(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID | None = None,
        elective_id: uuid.UUID | None = None,
        session_id: uuid.UUID | None = None,
        faculty_id: uuid.UUID | None = None,
        curriculum_id: uuid.UUID | None = None,
    ) -> None:
        import json
        import uuid as uuid_mod

        from sqlalchemy import text

        # 1. Tenant
        await db.execute(
            text("""
                INSERT INTO tenants (id, name, code, institution_type, regulatory_body, is_active, created_at, updated_at)
                VALUES (:id, 'JMN Test', :code, 'medical', 'NMC', true, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """),
            {"id": tenant_id, "code": f"T_{str(tenant_id)[:8]}"},
        )

        # Seed default prefix mapping
        prefix_map = {
            "AN": "ANAT",
            "PY": "PHYS",
            "BI": "BIOC",
            "MI": "MICR",
            "PA": "PATH",
            "PH": "PHAR",
            "FM": "FMED",
            "CM": "CMED",
        }
        await db.execute(
            text("""
                INSERT INTO mdm_configs (tenant_id, config_key, config_value, description)
                VALUES (:tenant_id, 'competency.prefix_to_subject_code', CAST(:config_value AS jsonb), 'Prefix mapping')
                ON CONFLICT (tenant_id, config_key) DO NOTHING
            """),
            {"tenant_id": tenant_id, "config_value": json.dumps(prefix_map)},
        )

        # Seed onboarding templates
        med_template = {
            "institution_type": "medical",
            "regulatory_body": "NMC",
            "departments": ["Anatomy", "Physiology"],
            "documents_required": ["NMC_Registration"],
        }
        nursing_template = {
            "institution_type": "nursing",
            "regulatory_body": "INC",
            "departments": ["Fundamentals of Nursing"],
            "documents_required": ["INC_Registration"],
        }
        await db.execute(
            text("""
                INSERT INTO mdm_configs (tenant_id, config_key, config_value, description)
                VALUES (:tenant_id, 'onboarding.template.medical', CAST(:med_value AS jsonb), 'Med onboarding')
                ON CONFLICT (tenant_id, config_key) DO NOTHING
            """),
            {"tenant_id": tenant_id, "med_value": json.dumps(med_template)},
        )
        await db.execute(
            text("""
                INSERT INTO mdm_configs (tenant_id, config_key, config_value, description)
                VALUES (:tenant_id, 'onboarding.template.nursing', CAST(:nursing_value AS jsonb), 'Nursing onboarding')
                ON CONFLICT (tenant_id, config_key) DO NOTHING
            """),
            {"tenant_id": tenant_id, "nursing_value": json.dumps(nursing_template)},
        )

        # 2. Faculty
        if faculty_id:
            fac_user_id = uuid_mod.uuid4()
            await db.execute(
                text("""
                    INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
                    VALUES (:id, :tid, :email, 'Test Faculty', 'hashed', true)
                    ON CONFLICT (id) DO NOTHING
                """),
                {"id": fac_user_id, "tid": tenant_id, "email": f"fac_{fac_user_id}@test.com"},
            )
            await db.execute(
                text("""
                    INSERT INTO faculty (id, tenant_id, user_id, employee_id, designation, department_id, status)
                    VALUES (:id, :tid, :uid, :emp, 'Professor', :dept, 'active')
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": faculty_id,
                    "tid": tenant_id,
                    "uid": fac_user_id,
                    "emp": f"EMP_{str(faculty_id)[:8]}",
                    "dept": None,
                },
            )

        # 3. Curriculum / Program / Academic Year / Batch
        ay_id = uuid_mod.uuid4()
        prog_id = uuid_mod.uuid4()
        await db.execute(
            text("""
                INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current)
                VALUES (:id, :tid, '2024-25', '2024-08-01', '2025-07-31', true)
                ON CONFLICT DO NOTHING
            """),
            {"id": ay_id, "tid": tenant_id},
        )
        await db.execute(
            text("""
                INSERT INTO programs (id, tenant_id, name, code, type, duration_years)
                VALUES (:id, :tid, 'MBBS', 'MBBS', 'professional_phase', 4)
                ON CONFLICT DO NOTHING
            """),
            {"id": prog_id, "tid": tenant_id},
        )

        curr_id = curriculum_id or uuid_mod.uuid4()
        await db.execute(
            text("""
                INSERT INTO curricula (id, tenant_id, program_id, name, version_code)
                VALUES (:id, :tid, :pid, 'CBME 2023', '2023')
                ON CONFLICT DO NOTHING
            """),
            {"id": curr_id, "tid": tenant_id, "pid": prog_id},
        )

        batch_id = uuid_mod.uuid4()
        await db.execute(
            text("""
                INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code)
                VALUES (:id, :tid, :ayid, :pid, 'MBBS-2024', 'MBBS2024')
                ON CONFLICT DO NOTHING
            """),
            {"id": batch_id, "tid": tenant_id, "pid": prog_id, "ayid": ay_id},
        )

        # 4. Student
        if student_id:
            stud_user_id = student_id
            await db.execute(
                text("""
                    INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
                    VALUES (:id, :tid, :email, 'Test Student', 'hashed', true)
                    ON CONFLICT ON CONSTRAINT users_pkey DO NOTHING
                """),
                {"id": stud_user_id, "tid": tenant_id, "email": f"student_{stud_user_id}@test.com"},
            )
            await db.execute(
                text("""
                    INSERT INTO students (id, tenant_id, user_id, batch_id, roll_number, admission_year, status)
                    VALUES (:id, :tid, :uid, :bid, :roll, 2024, 'active')
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": student_id,
                    "tid": tenant_id,
                    "uid": stud_user_id,
                    "bid": batch_id,
                    "roll": f"R_{str(student_id)[:8]}",
                },
            )

        # 5. Session
        if session_id:
            course_id = uuid_mod.uuid4()
            await db.execute(
                text("""
                    INSERT INTO courses (id, tenant_id, name, code, department_id)
                    VALUES (:id, :tid, 'Anatomy', 'ANAT', NULL)
                    ON CONFLICT DO NOTHING
                """),
                {"id": course_id, "tid": tenant_id},
            )
            lp_id = uuid_mod.uuid4()
            await db.execute(
                text("""
                    INSERT INTO lesson_plans (id, tenant_id, curriculum_id, course_id, topic, competency_code, hours, method)
                    VALUES (:id, :tid, :curid, :cid, 'Topic', 'AN1.1', 1.0, 'lecture')
                    ON CONFLICT DO NOTHING
                """),
                {"id": lp_id, "tid": tenant_id, "curid": curr_id, "cid": course_id},
            )
            await db.execute(
                text("""
                    INSERT INTO sessions (id, tenant_id, lesson_plan_id, session_date, status)
                    VALUES (:id, :tid, :lpid, CURRENT_DATE, 'scheduled')
                    ON CONFLICT DO NOTHING
                """),
                {"id": session_id, "tid": tenant_id, "lpid": lp_id},
            )

        # 6. Elective
        if elective_id:
            await db.execute(
                text("""
                    INSERT INTO electives (id, tenant_id, curriculum_id, code, title, block, elective_type, capacity)
                    VALUES (:id, :tid, :curid, :code, 'Elective', 'Block 1', 'clinical', 10)
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": elective_id,
                    "tid": tenant_id,
                    "curid": curr_id,
                    "code": f"ELEC_{str(elective_id)[:8]}",
                },
            )

        await db.commit()

    return _seed
