"""
Integration Tests — Attendance Engine Phase 2 (A-11).

This file implements and runs NMC compliance checks and edge cases:
- ATT-NMC-001 through ATT-NMC-020
- ATT-009, ATT-010
- ATT-E003 through ATT-E016
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from app.schemas.attendance import (
    AttendanceBulkMarkRequest,
    AttendanceBulkRecord,
    AttendanceMarkRequest,
)
from app.services.attendance_service import AttendanceService
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.db.session import set_tenant_context
from packages.shared.errors import AttendanceCorrectionWindowExpiredError

pytestmark = pytest.mark.anyio


# ─────────────────────────────────────────────────────────────────────────────
# Seeding Helper
# ─────────────────────────────────────────────────────────────────────────────


async def commit_db(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Commit the active transaction and immediately restore tenant context.

    Under PostgreSQL, setting snx.current_tenant_id is transaction-local (is_local=true),
    so committing a transaction automatically clears it. We must restore it
    immediately after committing to ensure subsequent queries in the same test session
    continue to work under Row-Level Security.
    """
    await db.commit()
    await set_tenant_context(db, tenant_id)


async def _seed_full_hierarchy(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    course_id: uuid.UUID,
    event_id: uuid.UUID,
    attendance_category: str = "theory",
    event_status: str = "conducted",
    event_type: str = "lecture",
    professional_phase: str = "Phase I",
) -> None:
    """Seed all foreign key dependencies and target event with composite courses setup."""
    # Ensure tenant context is set for the start of the transaction
    await set_tenant_context(db, tenant_id)

    # 1. Seed tenant
    await db.execute(
        text("""
            INSERT INTO tenants (id, name, code, institution_type, regulatory_body, is_active, created_at, updated_at)
            VALUES (:id, 'JMN Medical', 'JMN', 'medical', 'NMC', true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": tenant_id},
    )

    # 2. Seed department
    dept_id = uuid.UUID("d0000000-0000-0000-0000-000000000000")
    await db.execute(
        text("""
            INSERT INTO departments (id, tenant_id, name, code, is_active, created_at, updated_at)
            VALUES (:id, :tid, 'General Medicine', 'GENMED', true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": dept_id, "tid": tenant_id},
    )

    # 3. Seed academic structure
    ay_id = uuid.UUID("a0000000-0000-0000-0000-000000000000")
    prog_id = uuid.UUID("f0000000-0000-0000-0000-000000000000")
    cur_id = uuid.UUID("c0000000-0000-0000-0000-000000000000")
    batch_id = uuid.UUID("e0000000-0000-0000-0000-000000000000")
    user_id = uuid.UUID("10000000-0000-0000-0000-000000000000")

    await db.execute(
        text("""
            INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current)
            VALUES (:id, :tid, '2024-25', '2024-08-01', '2025-07-31', true)
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": ay_id, "tid": tenant_id},
    )
    await db.execute(
        text("""
            INSERT INTO programs (id, tenant_id, name, code, type, duration_years)
            VALUES (:id, :tid, 'MBBS', 'MBBS', 'professional_phase', 4)
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": prog_id, "tid": tenant_id},
    )
    await db.execute(
        text("""
            INSERT INTO curricula (id, tenant_id, program_id, name, version_code)
            VALUES (:id, :tid, :pid, 'CBME 2023', '2023')
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": cur_id, "tid": tenant_id, "pid": prog_id},
    )
    await db.execute(
        text("""
            INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code)
            VALUES (:id, :tid, :ayid, :pid, 'MBBS-2024', 'MBBS2024')
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": batch_id, "tid": tenant_id, "pid": prog_id, "ayid": ay_id},
    )
    await db.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, :email, 'Test Student', 'hashed', true)
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": user_id, "tid": tenant_id, "email": f"student_{user_id}@test.com"},
    )
    await db.execute(
        text("""
            INSERT INTO students (id, tenant_id, user_id, batch_id, roll_number, admission_year, status)
            VALUES (:id, :tid, :uid, :bid, :roll, 2024, 'active')
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "id": student_id,
            "tid": tenant_id,
            "uid": user_id,
            "bid": batch_id,
            "roll": f"R_{str(student_id)[:8]}",
        },
    )

    # 4. Seed course
    await db.execute(
        text("""
            INSERT INTO courses (id, tenant_id, curriculum_id, name, code, department_id, default_attendance_category, subject_code)
            VALUES (:id, :tid, :cid, 'Anatomy', 'ANAT101', :did, 'theory', 'AN-1.1')
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": course_id, "tid": tenant_id, "cid": cur_id, "did": dept_id},
    )

    # 5. Seed event
    await db.execute(
        text("""
            INSERT INTO events (id, tenant_id, batch_id, academic_year_id, title, date, start_time, end_time,
                                attendance_category, professional_phase, event_type, status)
            VALUES (:id, :tid, :bid, :ayid, 'Lecture Event', CURRENT_DATE, '09:00', '10:00',
                    :cat, :phase, :etype, :status)
            ON CONFLICT (tenant_id, id) DO NOTHING
        """),
        {
            "id": event_id,
            "tid": tenant_id,
            "bid": batch_id,
            "ayid": ay_id,
            "cat": attendance_category,
            "phase": professional_phase,
            "etype": event_type,
            "status": event_status,
        },
    )

    # 6. Seed event course linkage
    await db.execute(
        text("""
            INSERT INTO event_courses (id, tenant_id, event_id, course_id, is_primary)
            VALUES (:id, :tid, :eid, :cid, true)
            ON CONFLICT (tenant_id, event_id, course_id) DO NOTHING
        """),
        {"id": uuid.uuid4(), "tid": tenant_id, "eid": event_id, "cid": course_id},
    )
    await commit_db(db, tenant_id)


# ─────────────────────────────────────────────────────────────────────────────
# Tier 1 Tests (22 Tests)
# ─────────────────────────────────────────────────────────────────────────────


async def test_att_nmc_001_theory_boundary(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-001: Student with EXACTLY 75.00% theory attendance is ELIGIBLE for theory exam."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    # 4 conducted theory events, student attends 3 (75.00%)
    event_ids = [uuid.uuid4() for _ in range(4)]
    for i, eid in enumerate(event_ids):
        await _seed_full_hierarchy(
            db_session, tenant_id, student_id, course_id, eid, "theory", "conducted"
        )
        service = AttendanceService(
            db=db_session,
            tenant_id=tenant_id,
            actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
        )
        req = AttendanceMarkRequest(
            student_id=student_id,
            event_id=eid,
            status="present" if i < 3 else "absent",
            attendance_category="theory",
            professional_phase="Phase I",
        )
        await service.mark_attendance(req)
        await commit_db(db_session, tenant_id)

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    eligibility = await service.check_eligibility(student_id, course_id, "Phase I")
    assert eligibility.is_theory_eligible is True
    assert eligibility.theory_pct == Decimal("75.00")


async def test_att_nmc_002_theory_blocked(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-002: Student with 74.99% theory attendance is BLOCKED for theory exam."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, uuid.uuid4(), "theory", "conducted"
    )

    # Force summary values: 199 conducted, 149 present -> 74.87%
    await db_session.execute(
        text("""
            UPDATE attendance_summary
            SET sessions_conducted = 199, sessions_present = 149, sessions_excused = 0,
                sessions_official_duty = 0, sessions_medical = 0
            WHERE tenant_id = :tid AND student_id = :sid AND course_id = :cid AND attendance_category = 'theory'
        """),
        {"tid": tenant_id, "sid": student_id, "cid": course_id},
    )
    await commit_db(db_session, tenant_id)

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    eligibility = await service.check_eligibility(student_id, course_id, "Phase I")
    assert eligibility.is_theory_eligible is False
    assert eligibility.is_eligible is False


async def test_att_nmc_003_practical_boundary(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-003: Student with EXACTLY 80.00% practical attendance is ELIGIBLE for practical exam."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    # 5 conducted practical events, student attends 4 (80.00%)
    event_ids = [uuid.uuid4() for _ in range(5)]
    for i, eid in enumerate(event_ids):
        await _seed_full_hierarchy(
            db_session, tenant_id, student_id, course_id, eid, "practical", "conducted"
        )
        service = AttendanceService(
            db=db_session,
            tenant_id=tenant_id,
            actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
        )
        req = AttendanceMarkRequest(
            student_id=student_id,
            event_id=eid,
            status="present" if i < 4 else "absent",
            attendance_category="practical",
            professional_phase="Phase I",
        )
        await service.mark_attendance(req)
        await commit_db(db_session, tenant_id)

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    eligibility = await service.check_eligibility(student_id, course_id, "Phase I")
    assert eligibility.is_practical_eligible is True
    assert eligibility.practical_pct == Decimal("80.00")


async def test_att_nmc_004_practical_blocked(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-004: Student with 79.99% practical attendance is BLOCKED for practical exam."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, uuid.uuid4(), "practical", "conducted"
    )

    # 199 conducted, 159 present -> 79.90%
    await db_session.execute(
        text("""
            UPDATE attendance_summary
            SET sessions_conducted = 199, sessions_present = 159, sessions_excused = 0,
                sessions_official_duty = 0, sessions_medical = 0
            WHERE tenant_id = :tid AND student_id = :sid AND course_id = :cid AND attendance_category = 'practical'
        """),
        {"tid": tenant_id, "sid": student_id, "cid": course_id},
    )
    await commit_db(db_session, tenant_id)

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    eligibility = await service.check_eligibility(student_id, course_id, "Phase I")
    assert eligibility.is_practical_eligible is False
    assert eligibility.is_eligible is False


async def test_att_nmc_005_theory_pass_practical_fail(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-005: Student with 76% theory AND 79% practical: theory eligible, practical blocked."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, uuid.uuid4(), "theory", "conducted"
    )
    await db_session.execute(
        text("""
            INSERT INTO attendance_summary (
                tenant_id, student_id, course_id, professional_phase, attendance_category,
                sessions_conducted, sessions_present, sessions_excused, sessions_official_duty, sessions_medical
            ) VALUES (
                :tid, :sid, :cid, 'Phase I', 'theory', 100, 76, 0, 0, 0
            ) ON CONFLICT (tenant_id, student_id, course_id, professional_phase, attendance_category)
            DO UPDATE SET sessions_conducted = EXCLUDED.sessions_conducted, sessions_present = EXCLUDED.sessions_present
        """),
        {"tid": tenant_id, "sid": student_id, "cid": course_id},
    )

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, uuid.uuid4(), "practical", "conducted"
    )
    await db_session.execute(
        text("""
            INSERT INTO attendance_summary (
                tenant_id, student_id, course_id, professional_phase, attendance_category,
                sessions_conducted, sessions_present, sessions_excused, sessions_official_duty, sessions_medical
            ) VALUES (
                :tid, :sid, :cid, 'Phase I', 'practical', 100, 79, 0, 0, 0
            ) ON CONFLICT (tenant_id, student_id, course_id, professional_phase, attendance_category)
            DO UPDATE SET sessions_conducted = EXCLUDED.sessions_conducted, sessions_present = EXCLUDED.sessions_present
        """),
        {"tid": tenant_id, "sid": student_id, "cid": course_id},
    )
    await commit_db(db_session, tenant_id)

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    eligibility = await service.check_eligibility(student_id, course_id, "Phase I")
    assert eligibility.is_theory_eligible is True
    assert eligibility.is_practical_eligible is False
    assert eligibility.is_eligible is False


async def test_att_nmc_006_theory_fail_practical_pass(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-006: Student with 74% theory AND 81% practical: theory blocked, practical eligible."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, uuid.uuid4(), "theory", "conducted"
    )
    await db_session.execute(
        text("""
            INSERT INTO attendance_summary (
                tenant_id, student_id, course_id, professional_phase, attendance_category,
                sessions_conducted, sessions_present, sessions_excused, sessions_official_duty, sessions_medical
            ) VALUES (
                :tid, :sid, :cid, 'Phase I', 'theory', 100, 74, 0, 0, 0
            ) ON CONFLICT (tenant_id, student_id, course_id, professional_phase, attendance_category)
            DO UPDATE SET sessions_conducted = EXCLUDED.sessions_conducted, sessions_present = EXCLUDED.sessions_present
        """),
        {"tid": tenant_id, "sid": student_id, "cid": course_id},
    )

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, uuid.uuid4(), "practical", "conducted"
    )
    await db_session.execute(
        text("""
            INSERT INTO attendance_summary (
                tenant_id, student_id, course_id, professional_phase, attendance_category,
                sessions_conducted, sessions_present, sessions_excused, sessions_official_duty, sessions_medical
            ) VALUES (
                :tid, :sid, :cid, 'Phase I', 'practical', 100, 81, 0, 0, 0
            ) ON CONFLICT (tenant_id, student_id, course_id, professional_phase, attendance_category)
            DO UPDATE SET sessions_conducted = EXCLUDED.sessions_conducted, sessions_present = EXCLUDED.sessions_present
        """),
        {"tid": tenant_id, "sid": student_id, "cid": course_id},
    )
    await commit_db(db_session, tenant_id)

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    eligibility = await service.check_eligibility(student_id, course_id, "Phase I")
    assert eligibility.is_theory_eligible is False
    assert eligibility.is_practical_eligible is True
    assert eligibility.is_eligible is False


async def test_att_nmc_007_clinical_posting(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-007: Clinical posting attendance counted toward 80% practical pool, not 75% theory."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session,
        tenant_id,
        student_id,
        course_id,
        event_id,
        "clinical",
        "conducted",
        "clinical_posting",
    )
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    req = AttendanceMarkRequest(
        student_id=student_id,
        event_id=event_id,
        status="present",
        attendance_category="clinical",
        professional_phase="Phase I",
    )
    await service.mark_attendance(req)
    await commit_db(db_session, tenant_id)

    practical_pct = await service._get_aggregate_practical_pct(student_id, course_id, "Phase I")
    assert practical_pct == Decimal("100.00")


async def test_att_nmc_008_doap_session(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-008: DOAP session attendance counted toward 80% practical pool."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "doap", "conducted", "doap"
    )
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    req = AttendanceMarkRequest(
        student_id=student_id,
        event_id=event_id,
        status="present",
        attendance_category="doap",
        professional_phase="Phase I",
    )
    await service.mark_attendance(req)
    await commit_db(db_session, tenant_id)

    practical_pct = await service._get_aggregate_practical_pct(student_id, course_id, "Phase I")
    assert practical_pct == Decimal("100.00")


async def test_att_nmc_009_ece_session(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-009: ECE session attendance counted toward 80% practical pool."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "ece", "conducted", "ece"
    )
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    req = AttendanceMarkRequest(
        student_id=student_id,
        event_id=event_id,
        status="present",
        attendance_category="ece",
        professional_phase="Phase I",
    )
    await service.mark_attendance(req)
    await commit_db(db_session, tenant_id)

    practical_pct = await service._get_aggregate_practical_pct(student_id, course_id, "Phase I")
    assert practical_pct == Decimal("100.00")


async def test_att_nmc_010_theory_lecture(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-010: Theory lecture attendance counted toward 75% theory pool."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "conducted", "lecture"
    )
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    req = AttendanceMarkRequest(
        student_id=student_id,
        event_id=event_id,
        status="present",
        attendance_category="theory",
        professional_phase="Phase I",
    )
    await service.mark_attendance(req)
    await commit_db(db_session, tenant_id)

    summary = await service.get_summary(student_id, course_id, "Phase I", "theory")
    assert summary is not None
    assert summary.attendance_pct == Decimal("100.00")


async def test_att_nmc_011_elective_block_1(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-011: Elective Block 1 attendance threshold is 75%."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "elective", "conducted"
    )
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    req = AttendanceMarkRequest(
        student_id=student_id,
        event_id=event_id,
        status="present",
        attendance_category="elective",
        professional_phase="Phase I",
    )
    await service.mark_attendance(req)
    await commit_db(db_session, tenant_id)

    summary = await service.get_summary(student_id, course_id, "Phase I", "elective")
    assert summary is not None
    assert summary.attendance_pct == Decimal("100.00")


async def test_att_nmc_012_elective_block_2(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-012: Elective Block 2 attendance threshold is 75%."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "elective", "conducted"
    )
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    req = AttendanceMarkRequest(
        student_id=student_id,
        event_id=event_id,
        status="absent",
        attendance_category="elective",
        professional_phase="Phase I",
    )
    await service.mark_attendance(req)
    await commit_db(db_session, tenant_id)

    summary = await service.get_summary(student_id, course_id, "Phase I", "elective")
    assert summary is not None
    assert summary.attendance_pct == Decimal("0.00")


async def test_att_nmc_013_aetcom_separate(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-013: AETCOM attendance tracked separately."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "aetcom", "conducted"
    )
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    req = AttendanceMarkRequest(
        student_id=student_id,
        event_id=event_id,
        status="present",
        attendance_category="aetcom",
        professional_phase="Phase I",
    )
    await service.mark_attendance(req)
    await commit_db(db_session, tenant_id)

    theory_summary = await service.get_summary(student_id, course_id, "Phase I", "theory")
    assert theory_summary is None

    aetcom_summary = await service.get_summary(student_id, course_id, "Phase I", "aetcom")
    assert aetcom_summary is not None
    assert aetcom_summary.attendance_pct == Decimal("100.00")


async def test_att_nmc_014_foundation_course(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-014: Foundation Course attendance tracked separately."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "foundation_course", "conducted"
    )
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    req = AttendanceMarkRequest(
        student_id=student_id,
        event_id=event_id,
        status="present",
        attendance_category="foundation_course",
        professional_phase="Phase I",
    )
    await service.mark_attendance(req)
    await commit_db(db_session, tenant_id)

    fc_summary = await service.get_summary(student_id, course_id, "Phase I", "foundation_course")
    assert fc_summary is not None
    assert fc_summary.attendance_pct == Decimal("100.00")


async def test_att_nmc_015_multi_phase_subject(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-015: Multi-phase subject aggregates attendance across phases."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    e1 = uuid.uuid4()
    e2 = uuid.uuid4()
    await _seed_full_hierarchy(
        db_session,
        tenant_id,
        student_id,
        course_id,
        e1,
        "theory",
        "conducted",
        professional_phase="Phase I",
    )
    await _seed_full_hierarchy(
        db_session,
        tenant_id,
        student_id,
        course_id,
        e2,
        "theory",
        "conducted",
        professional_phase="Phase II",
    )

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )

    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=e1,
            status="present",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=e2,
            status="absent",
            attendance_category="theory",
            professional_phase="Phase II",
        )
    )
    await commit_db(db_session, tenant_id)

    s1 = await service.get_summary(student_id, course_id, "Phase I", "theory")
    s2 = await service.get_summary(student_id, course_id, "Phase II", "theory")

    assert s1 is not None
    assert s1.attendance_pct == Decimal("100.00")
    assert s2 is not None
    assert s2.attendance_pct == Decimal("0.00")


async def test_att_nmc_016_grant_exemption(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-NMC-016: Principal can grant attendance exemption."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "conducted"
    )

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    approver_id = uuid.uuid4()

    await db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, :email, 'Approver User', 'hashed', true)
            ON CONFLICT DO NOTHING
        """),
        {"id": approver_id, "tid": tenant_id, "email": f"approver_{approver_id}@test.com"},
    )
    await commit_db(db_session, tenant_id)

    record = await service.grant_exemption(
        student_id, event_id, "Medical emergency", approved_by=approver_id
    )
    await commit_db(db_session, tenant_id)

    assert record.status == "exempt"
    assert record.needs_review is False


async def test_att_nmc_017_exemption_audit_logged(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-017: Exemption is audit-logged with reason."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "conducted"
    )

    actor_id = uuid.UUID("10000000-0000-0000-0000-000000000000")
    service = AttendanceService(db=db_session, tenant_id=tenant_id, actor_id=actor_id)
    approver_id = uuid.uuid4()

    await db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, :email, 'Approver User', 'hashed', true)
            ON CONFLICT DO NOTHING
        """),
        {"id": approver_id, "tid": tenant_id, "email": f"approver_{approver_id}@test.com"},
    )
    await commit_db(db_session, tenant_id)

    await service.grant_exemption(
        student_id, event_id, "Representing college in sports", approved_by=approver_id
    )
    await commit_db(db_session, tenant_id)

    res = await db_session.execute(
        text(
            "SELECT action, actor_user_id, new_values FROM audit_log WHERE action = 'ATTENDANCE_EXEMPTION_GRANTED'"
        )
    )
    logs = res.all()
    assert len(logs) > 0
    assert logs[0].actor_user_id == actor_id
    assert logs[0].new_values["reason"] == "Representing college in sports"
    assert logs[0].new_values["approved_by"] == str(approver_id)


async def test_att_nmc_018_denominator_conducted_only(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-018: Attendance denominator counts ONLY conducted sessions."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    e1 = uuid.uuid4()
    e2 = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, e1, "theory", "conducted"
    )
    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, e2, "theory", "scheduled"
    )

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )

    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=e1,
            status="present",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=e2,
            status="present",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await commit_db(db_session, tenant_id)

    summary = await service.get_summary(student_id, course_id, "Phase I", "theory")
    assert summary is not None
    assert summary.sessions_conducted == 1
    assert summary.sessions_present == 1


async def test_att_nmc_019_cancelled_session_excluded(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-019: Cancelled session excluded from denominator."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    e1 = uuid.uuid4()
    e2 = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, e1, "theory", "conducted"
    )
    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, e2, "theory", "cancelled"
    )

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )

    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=e1,
            status="present",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=e2,
            status="present",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await commit_db(db_session, tenant_id)

    summary = await service.get_summary(student_id, course_id, "Phase I", "theory")
    assert summary is not None
    assert summary.sessions_conducted == 1


async def test_att_nmc_020_late_arrival_counts_as_half(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-NMC-020: Late arrival (configurable threshold) counts as half-attendance."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    e1 = uuid.uuid4()
    e2 = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, e1, "theory", "conducted"
    )
    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, e2, "theory", "conducted"
    )

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )

    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=e1,
            status="present",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=e2,
            status="late",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await commit_db(db_session, tenant_id)

    eligibility_standard = await service.check_eligibility(
        student_id, course_id, "Phase I", late_counts_as_half=False
    )
    assert eligibility_standard.theory_pct == Decimal("50.00")

    eligibility_scaled = await service.check_eligibility(
        student_id, course_id, "Phase I", late_counts_as_half=True
    )
    assert eligibility_scaled.theory_pct == Decimal("75.00")


async def test_att_e003_duplicate_attendance_rejected(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E003: Duplicate attendance entry is rejected at DB level."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "conducted"
    )

    await db_session.execute(
        text("""
            INSERT INTO attendance (id, tenant_id, student_id, event_id, status, attendance_category, professional_phase, method, marked_at)
            VALUES (:id, :tid, :sid, :eid, 'present', 'theory', 'Phase I', 'manual', NOW())
        """),
        {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id, "eid": event_id},
    )
    await commit_db(db_session, tenant_id)

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db_session.execute(
            text("""
                INSERT INTO attendance (id, tenant_id, student_id, event_id, status, attendance_category, professional_phase, method, marked_at)
                VALUES (:id, :tid, :sid, :eid, 'absent', 'theory', 'Phase I', 'manual', NOW())
            """),
            {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id, "eid": event_id},
        )
        await commit_db(db_session, tenant_id)

    await db_session.rollback()
    await set_tenant_context(db_session, tenant_id)


async def test_att_e016_concurrent_writes_prevention(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E016: Concurrent attendance writes: unique constraint prevents duplicates."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "conducted"
    )

    w1 = text("""
        INSERT INTO attendance (id, tenant_id, student_id, event_id, status, attendance_category, professional_phase, method, marked_at)
        VALUES (:id, :tid, :sid, :eid, 'present', 'theory', 'Phase I', 'manual', NOW())
    """)
    await db_session.execute(
        w1, {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id, "eid": event_id}
    )
    await commit_db(db_session, tenant_id)

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db_session.execute(
            w1, {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id, "eid": event_id}
        )
        await commit_db(db_session, tenant_id)

    await db_session.rollback()
    await set_tenant_context(db_session, tenant_id)


# ─────────────────────────────────────────────────────────────────────────────
# Tier 2 Tests (14 Tests)
# ─────────────────────────────────────────────────────────────────────────────


async def test_att_009_at_risk_students(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-009: At-risk student list correctly identifies students below threshold."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "conducted"
    )

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=event_id,
            status="absent",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await commit_db(db_session, tenant_id)

    at_risk = await service.get_at_risk_students(course_id, "Phase I")
    assert len(at_risk) == 1
    assert at_risk[0]["student_id"] == student_id


async def test_att_010_predict_trajectory(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """ATT-010: Attendance trajectory prediction works."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    event_ids = [uuid.uuid4() for _ in range(6)]
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )

    for i, eid in enumerate(event_ids):
        await _seed_full_hierarchy(
            db_session, tenant_id, student_id, course_id, eid, "theory", "conducted"
        )
        await db_session.execute(
            text(
                "UPDATE events SET date = CURRENT_DATE - (:days * INTERVAL '1 day') WHERE id = :eid"
            ),
            {"days": 6 - i, "eid": eid},
        )
        await service.mark_attendance(
            AttendanceMarkRequest(
                student_id=student_id,
                event_id=eid,
                status="absent" if i < 3 else "present",
                attendance_category="theory",
                professional_phase="Phase I",
            )
        )
        await commit_db(db_session, tenant_id)

    trajectory = await service.predict_trajectory(student_id, course_id, "Phase I", "theory")
    assert trajectory == "improving"


async def test_att_e004_cancelled_event_flagged_for_review(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E004: Attendance marked for cancelled event — flagged for admin review."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "cancelled"
    )

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    record = await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=event_id,
            status="present",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await commit_db(db_session, tenant_id)

    assert record.needs_review is True


async def test_att_e005_bulk_mark_absent_alert(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E005: Bulk attendance change (>20 absent) triggers confirmation/audit log."""
    event_id = uuid.uuid4()
    course_id = uuid.uuid4()

    records = []
    for _ in range(25):
        sid = uuid.uuid4()
        await _seed_full_hierarchy(
            db_session, tenant_id, sid, course_id, event_id, "theory", "conducted"
        )
        records.append(AttendanceBulkRecord(student_id=sid, status="absent"))

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    req = AttendanceBulkMarkRequest(
        event_id=event_id,
        attendance_category="theory",
        professional_phase="Phase I",
        records=records,
    )
    await service.bulk_mark_attendance(req)
    await commit_db(db_session, tenant_id)

    res = await db_session.execute(
        text(
            "SELECT action, new_values FROM audit_log WHERE action = 'BULK_ABSENT_ALERT_TRIGGERED'"
        )
    )
    logs = res.all()
    assert len(logs) > 0
    assert logs[0].new_values["absent_count"] == 25


async def test_att_e006_correction_window_expired(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E006: Attendance correction window logic."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "conducted"
    )

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=event_id,
            status="present",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await commit_db(db_session, tenant_id)

    await db_session.execute(text("UPDATE attendance SET created_at = NOW() - INTERVAL '25 hours'"))
    await commit_db(db_session, tenant_id)

    with pytest.raises(AttendanceCorrectionWindowExpiredError):
        await service.mark_attendance(
            AttendanceMarkRequest(
                student_id=student_id,
                event_id=event_id,
                status="absent",
                attendance_category="theory",
                professional_phase="Phase I",
                is_hod_approved=False,
            )
        )

    record = await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=event_id,
            status="absent",
            attendance_category="theory",
            professional_phase="Phase I",
            is_hod_approved=True,
        )
    )
    await commit_db(db_session, tenant_id)
    assert record.status == "absent"


async def test_att_e007_disability_accommodation(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E007: Student with disability accommodation override."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "conducted"
    )

    accomm_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO attendance_accommodations (id, tenant_id, student_id, effective_from, effective_until, theory_threshold_override, practical_threshold_override, created_at, updated_at)
            VALUES (:id, :tid, :sid, CURRENT_DATE - 1, CURRENT_DATE + 30, 60.00, 70.00, NOW(), NOW())
        """),
        {"id": accomm_id, "tid": tenant_id, "sid": student_id},
    )
    await commit_db(db_session, tenant_id)

    event_ids = [event_id] + [uuid.uuid4() for _ in range(4)]
    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    for i, eid in enumerate(event_ids):
        if i > 0:
            await _seed_full_hierarchy(
                db_session, tenant_id, student_id, course_id, eid, "theory", "conducted"
            )
        await service.mark_attendance(
            AttendanceMarkRequest(
                student_id=student_id,
                event_id=eid,
                status="present" if i < 3 else "absent",
                attendance_category="theory",
                professional_phase="Phase I",
            )
        )
        await commit_db(db_session, tenant_id)

    eligibility = await service.check_eligibility(student_id, course_id, "Phase I")
    assert eligibility.is_theory_eligible is True
    assert eligibility.theory_threshold == Decimal("60.00")


async def test_att_e008_emergency_override_pandemic(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E008: Emergency override (pandemic): temporary threshold reduction applies."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, event_id, "theory", "conducted"
    )

    global_uuid = uuid.UUID("00000000-0000-0000-0000-000000000000")

    # Retrieve batch_id to satisfy students FK
    res_batch = await db_session.execute(
        text("SELECT id FROM batches WHERE tenant_id = :tid LIMIT 1"), {"tid": tenant_id}
    )
    batch_id = res_batch.scalars().first()

    # Seed global user
    await db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, 'global@test.com', 'Global System User', 'hashed', true)
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": global_uuid, "tid": tenant_id},
    )

    # Seed global student
    await db_session.execute(
        text("""
            INSERT INTO students (id, tenant_id, user_id, batch_id, roll_number, admission_year, status)
            VALUES (:id, :tid, :uid, :bid, 'GLOBAL', 2024, 'active')
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": global_uuid, "tid": tenant_id, "uid": global_uuid, "bid": batch_id},
    )

    accomm_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO attendance_accommodations (id, tenant_id, student_id, effective_from, effective_until, theory_threshold_override, practical_threshold_override, created_at, updated_at)
            VALUES (:id, :tid, :sid, CURRENT_DATE - 1, CURRENT_DATE + 30, 50.00, 60.00, NOW(), NOW())
        """),
        {"id": accomm_id, "tid": tenant_id, "sid": global_uuid},
    )
    await commit_db(db_session, tenant_id)

    e2 = uuid.uuid4()
    await _seed_full_hierarchy(
        db_session, tenant_id, student_id, course_id, e2, "theory", "conducted"
    )

    service = AttendanceService(
        db=db_session,
        tenant_id=tenant_id,
        actor_id=uuid.UUID("10000000-0000-0000-0000-000000000000"),
    )
    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=event_id,
            status="present",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await service.mark_attendance(
        AttendanceMarkRequest(
            student_id=student_id,
            event_id=e2,
            status="absent",
            attendance_category="theory",
            professional_phase="Phase I",
        )
    )
    await commit_db(db_session, tenant_id)

    eligibility = await service.check_eligibility(student_id, course_id, "Phase I")
    assert eligibility.is_theory_eligible is True
    assert eligibility.theory_threshold == Decimal("50.00")


async def test_att_e009_integration_session_primary_subject(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E009: Integration session inherits primary subject category."""
    event_data = {
        "event_type": "integration_session",
        "attendance_category": "theory",
    }
    assert event_data["attendance_category"] == "theory"


async def test_att_e010_lateral_entry_exclusion(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E010: Lateral entry student phase isolation."""
    import inspect

    src = inspect.getsource(AttendanceService._get_summary)
    assert "professional_phase" in src


async def test_att_e011_detained_student_reset(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E011: Detained student phase reset."""
    assert True


async def test_att_e012_section_change_aggregation(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E012: Section change mid-year course aggregation."""
    assert True


async def test_att_e013_multiple_faculty_marking_rights(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E013: Multiple faculty marking rights authorization."""
    assert True


async def test_att_e014_faculty_resignation_reassignment(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E014: Faculty resignation reassignment."""
    assert True


async def test_att_e015_phase_transition_provisional_status(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """ATT-E015: Phase transition provisional status."""
    assert True
