"""FCS-001, FCS-002, AES-001: Foundation Course and AETCOM sync tests.

Tests cover DB-trigger driven sync behaviour:
- FCS-001: Foundation Course records completed_hours recomputed from attendance
- FCS-002: Trigger blocks completed_hours reduction if signoff received
- AES-001: AETCOM records status recomputed automatically from attendance
"""

from __future__ import annotations

import datetime
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.db.session import set_tenant_context


async def commit_db(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Commit and restore tenant context (transaction-local setting resets on commit)."""
    await db.commit()
    await set_tenant_context(db, tenant_id)


async def _seed_student_and_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    event_id: uuid.UUID,
    attendance_category: str = "foundation_course",
    event_duration_hours: float = 1.0,
) -> dict:
    """Seed minimal hierarchy for sync tests.

    Returns dict with all seeded IDs.
    """
    await set_tenant_context(db, tenant_id)

    dept_id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
    ay_id = uuid.UUID("a1000000-0000-0000-0000-000000000001")
    prog_id = uuid.UUID("f1000000-0000-0000-0000-000000000001")
    cur_id = uuid.UUID("c1000000-0000-0000-0000-000000000001")
    batch_id = uuid.UUID("e1000000-0000-0000-0000-000000000001")
    user_id = uuid.UUID("11000000-0000-0000-0000-000000000001")
    course_id = uuid.UUID("b1000000-0000-0000-0000-000000000001")

    await db.execute(
        text("""
            INSERT INTO tenants (id, name, code, institution_type, regulatory_body, is_active, created_at, updated_at)
            VALUES (:id, 'JMN Medical', 'JMN', 'medical', 'NMC', true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": tenant_id},
    )
    await db.execute(
        text("""
            INSERT INTO departments (id, tenant_id, name, code, is_active, created_at, updated_at)
            VALUES (:id, :tid, 'Foundation', 'FOUND', true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": dept_id, "tid": tenant_id},
    )
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
            VALUES (:id, :tid, 'MBBS', 'MBBS-SYNC', 'professional_phase', 4)
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": prog_id, "tid": tenant_id},
    )
    await db.execute(
        text("""
            INSERT INTO curricula (id, tenant_id, program_id, name, version_code)
            VALUES (:id, :tid, :pid, 'CBME 2023', 'CBME-2023-SYNC')
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": cur_id, "tid": tenant_id, "pid": prog_id},
    )
    await db.execute(
        text("""
            INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code)
            VALUES (:id, :tid, :ayid, :pid, 'MBBS-SYNC', 'MBBSSYNC')
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": batch_id, "tid": tenant_id, "pid": prog_id, "ayid": ay_id},
    )
    await db.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, :email, 'Sync Student', 'hashed', true)
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": user_id, "tid": tenant_id, "email": f"sync_{user_id}@test.com"},
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
            "roll": f"RS_{str(student_id)[:8]}",
        },
    )
    await db.execute(
        text("""
            INSERT INTO courses (id, tenant_id, curriculum_id, name, code, department_id, default_attendance_category, subject_code)
            VALUES (:id, :tid, :cid, 'Foundation Module', 'FOUND101', :did, :cat, 'FD-1.1')
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "id": course_id,
            "tid": tenant_id,
            "cid": cur_id,
            "did": dept_id,
            "cat": attendance_category,
        },
    )

    # Calculate event times based on desired duration
    start_time = datetime.time(9, 0)
    end_hour = 9 + int(event_duration_hours)
    end_min = int((event_duration_hours - int(event_duration_hours)) * 60)
    end_time = datetime.time(end_hour, end_min)

    await db.execute(
        text("""
            INSERT INTO events (id, tenant_id, batch_id, academic_year_id, title, date, start_time, end_time,
                                attendance_category, professional_phase, event_type, status)
            VALUES (:id, :tid, :bid, :ayid, 'Foundation Session', CURRENT_DATE, :st, :et,
                    :cat, 'Phase I', 'lecture', 'conducted')
            ON CONFLICT (tenant_id, id) DO NOTHING
        """),
        {
            "id": event_id,
            "tid": tenant_id,
            "bid": batch_id,
            "ayid": ay_id,
            "cat": attendance_category,
            "st": start_time,
            "et": end_time,
        },
    )
    await db.execute(
        text("""
            INSERT INTO event_courses (id, tenant_id, event_id, course_id, is_primary)
            VALUES (:id, :tid, :eid, :cid, true)
            ON CONFLICT (tenant_id, event_id, course_id) DO NOTHING
        """),
        {
            "id": uuid.uuid4(),
            "tid": tenant_id,
            "eid": event_id,
            "cid": course_id,
        },
    )
    await commit_db(db, tenant_id)

    return {
        "dept_id": dept_id,
        "ay_id": ay_id,
        "prog_id": prog_id,
        "cur_id": cur_id,
        "batch_id": batch_id,
        "user_id": user_id,
        "course_id": course_id,
    }


@pytest.mark.anyio
async def test_fcs_001_foundation_hours_recomputed_from_attendance(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """FCS-001: Foundation Course records completed_hours recomputed automatically from attendance."""
    student_id = uuid.uuid4()
    event_id = uuid.uuid4()

    await _seed_student_and_event(
        db_session, tenant_id, student_id, event_id, "foundation_course", 2.0
    )

    # Seed foundation_course_records row (required_hours = 4, completed_hours starts at 0)
    fcr_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO foundation_course_records (id, tenant_id, student_id, module_name, required_hours, completed_hours)
            VALUES (:id, :tid, :sid, 'orientation', 4.00, 0.00)
        """),
        {"id": fcr_id, "tid": tenant_id, "sid": student_id},
    )
    await commit_db(db_session, tenant_id)

    # Mark attendance as present for 2-hour foundation_course event → trigger should update completed_hours
    await db_session.execute(
        text("""
            INSERT INTO attendance (
                tenant_id, student_id, event_id, status, attendance_category,
                professional_phase, method, marked_at, original_marked_at
            ) VALUES (
                :tid, :sid, :eid, 'present', 'foundation_course',
                'Phase I', 'manual', NOW(), NOW()
            )
        """),
        {"tid": tenant_id, "sid": student_id, "eid": event_id},
    )
    await commit_db(db_session, tenant_id)

    # Assert trigger updated completed_hours
    result = await db_session.execute(
        text("SELECT completed_hours FROM foundation_course_records WHERE id = :id"),
        {"id": fcr_id},
    )
    row = result.mappings().first()
    assert row is not None, "FCS-001: foundation_course_records row not found"
    # The event is 2 hours (09:00-11:00); completed_hours should now be 2.00
    assert float(row["completed_hours"]) == pytest.approx(
        2.0, abs=0.01
    ), f"FCS-001: completed_hours not recomputed; got {row['completed_hours']}"


@pytest.mark.anyio
async def test_fcs_002_trigger_blocks_hours_reduction_after_signoff(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """FCS-002: Trigger blocks completed_hours reduction if signoff received (logs COMPLIANCE_INCIDENT)."""
    student_id = uuid.uuid4()
    event_id = uuid.uuid4()

    ids = await _seed_student_and_event(
        db_session, tenant_id, student_id, event_id, "foundation_course", 2.0
    )

    # Seed foundation_course_records with signoff already received and completed_hours = 4.00
    fcr_id = uuid.uuid4()
    faculty_id = uuid.uuid4()
    # Seed a faculty user for signed_off_by FK
    fac_user_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, :email, 'Faculty Sign', 'hashed', true)
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": fac_user_id, "tid": tenant_id, "email": f"fac_{fac_user_id}@test.com"},
    )
    await db_session.execute(
        text("""
            INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id, is_active)
            VALUES (:id, :tid, :uid, :did, 'Professor', :empid, true)
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "id": faculty_id,
            "tid": tenant_id,
            "uid": fac_user_id,
            "did": ids["dept_id"],
            "empid": f"EMP{str(faculty_id)[:6]}",
        },
    )
    await db_session.execute(
        text("""
            INSERT INTO foundation_course_records (id, tenant_id, student_id, module_name,
                required_hours, completed_hours, is_completed, signoff_received_at, signed_off_by)
            VALUES (:id, :tid, :sid, 'orientation', 4.00, 4.00, true, NOW(), :fid)
        """),
        {"id": fcr_id, "tid": tenant_id, "sid": student_id, "fid": faculty_id},
    )
    await commit_db(db_session, tenant_id)

    # Now mark attendance as absent (or delete present) — would lower completed_hours below required
    # Insert then delete the attendance to trigger a reduction
    await db_session.execute(
        text("""
            INSERT INTO attendance (
                tenant_id, student_id, event_id, status, attendance_category,
                professional_phase, method, marked_at, original_marked_at
            ) VALUES (
                :tid, :sid, :eid, 'present', 'foundation_course',
                'Phase I', 'manual', NOW(), NOW()
            )
        """),
        {"tid": tenant_id, "sid": student_id, "eid": event_id},
    )
    await commit_db(db_session, tenant_id)

    # Soft-delete the attendance → trigger fires, sees completed_hours would drop, logs COMPLIANCE_INCIDENT
    await db_session.execute(
        text("""
            UPDATE attendance SET deleted_at = NOW(), status = 'absent'
            WHERE tenant_id = :tid AND student_id = :sid AND event_id = :eid
        """),
        {"tid": tenant_id, "sid": student_id, "eid": event_id},
    )
    await commit_db(db_session, tenant_id)

    # Check that an audit_log entry with COMPLIANCE_INCIDENT was created
    result = await db_session.execute(
        text("""
            SELECT action FROM audit_log
            WHERE tenant_id = :tid
              AND action = 'COMPLIANCE_INCIDENT'
              AND resource_type = 'foundation_course_exemption'
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"tid": tenant_id},
    )
    row = result.mappings().first()
    assert (
        row is not None
    ), "FCS-002: Expected COMPLIANCE_INCIDENT audit entry when hours dropped below signoff limit"
    assert row["action"] == "COMPLIANCE_INCIDENT"


@pytest.mark.anyio
async def test_aes_001_aetcom_status_recomputed_from_attendance(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """AES-001: AETCOM records status recomputed automatically from attendance."""
    student_id = uuid.uuid4()
    event_id = uuid.uuid4()

    ids = await _seed_student_and_event(db_session, tenant_id, student_id, event_id, "aetcom", 1.0)

    # Seed a lesson_plan with a competency_code
    lp_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO lesson_plans (
                id, tenant_id, course_id, curriculum_id, code, version, is_current,
                topic, estimated_hours, competency_code, nmc_competency_level, is_core, status
            ) VALUES (
                :id, :tid, :cid, :curid, 'AET-LP-001', 1, true,
                'AETCOM Module 1', 1.0, 'AE-1.1', 'K', true, 'approved'
            )
        """),
        {
            "id": lp_id,
            "tid": tenant_id,
            "cid": ids["course_id"],
            "curid": ids["cur_id"],
        },
    )
    await commit_db(db_session, tenant_id)

    # Seed a session referencing this lesson_plan
    session_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO sessions (
                id, tenant_id, event_id, lesson_plan_id, conducted_at, actual_hours
            ) VALUES (
                :id, :tid, :eid, :lpid, NOW(), 1.0
            )
        """),
        {"id": session_id, "tid": tenant_id, "eid": event_id, "lpid": lp_id},
    )
    await commit_db(db_session, tenant_id)

    # Seed aetcom_records row with status='pending' for this student + competency
    aetcom_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO aetcom_records (
                id, tenant_id, student_id, module_code, competency_code, professional_phase, status
            ) VALUES (
                :id, :tid, :sid, 'AET-MOD1', 'AE-1.1', 'Phase I', 'pending'
            )
        """),
        {"id": aetcom_id, "tid": tenant_id, "sid": student_id},
    )
    await commit_db(db_session, tenant_id)

    # Mark attendance as 'present' for the AETCOM event + session_id → trigger fires
    await db_session.execute(
        text("""
            INSERT INTO attendance (
                tenant_id, student_id, event_id, session_id, status, attendance_category,
                professional_phase, method, marked_at, original_marked_at
            ) VALUES (
                :tid, :sid, :eid, :ses_id, 'present', 'aetcom',
                'Phase I', 'manual', NOW(), NOW()
            )
        """),
        {
            "tid": tenant_id,
            "sid": student_id,
            "eid": event_id,
            "ses_id": session_id,
        },
    )
    await commit_db(db_session, tenant_id)

    # Assert aetcom_records status updated to 'reflection_submitted'
    result = await db_session.execute(
        text("SELECT status FROM aetcom_records WHERE id = :id"),
        {"id": aetcom_id},
    )
    row = result.mappings().first()
    assert row is not None, "AES-001: aetcom_records row not found"
    assert (
        row["status"] == "reflection_submitted"
    ), f"AES-001: Expected 'reflection_submitted', got '{row['status']}'"


# =============================================================================
# Phase C — Cross-Module Integration Scenarios
# =============================================================================


@pytest.mark.anyio
async def test_phase_c_leave_to_attendance_materialization(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """Phase C: Leave approval → attendance materialization via DB trigger.

    When an event is inserted for a batch on a date covered by an approved leave request,
    the trigger trg_events_after_insert_leave automatically inserts attendance rows
    with status 'excused' (or 'medical' for medical leave) for each eligible student.
    """
    student_id = uuid.uuid4()
    event_id = uuid.uuid4()

    ids = await _seed_student_and_event(db_session, tenant_id, student_id, event_id, "theory", 1.0)

    # Seed an approved leave request covering today
    leave_id = uuid.uuid4()
    today = datetime.date.today()
    await db_session.execute(
        text("""
            INSERT INTO leave_requests (
                id, tenant_id, student_id, leave_type, start_date, end_date,
                reason, status, created_at, updated_at
            ) VALUES (
                :id, :tid, :sid, 'medical', :start, :end,
                'Illness', 'approved', NOW(), NOW()
            )
        """),
        {
            "id": leave_id,
            "tid": tenant_id,
            "sid": student_id,
            "start": today,
            "end": today,
        },
    )
    await commit_db(db_session, tenant_id)

    # Insert a new event on today's date — trigger should auto-insert attendance as 'medical'
    new_event_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO events (
                id, tenant_id, batch_id, academic_year_id, title, date, start_time, end_time,
                attendance_category, professional_phase, event_type, status
            ) VALUES (
                :id, :tid, :bid, :ayid, 'Auto Attendance Test', :dt, '14:00', '15:00',
                'theory', 'Phase I', 'lecture', 'conducted'
            )
        """),
        {
            "id": new_event_id,
            "tid": tenant_id,
            "bid": ids["batch_id"],
            "ayid": ids["ay_id"],
            "dt": today,
        },
    )
    await commit_db(db_session, tenant_id)

    # Check that attendance was auto-inserted for this student with 'medical' status
    result = await db_session.execute(
        text("""
            SELECT status, attendance_category, leave_request_id
            FROM attendance
            WHERE tenant_id = :tid
              AND student_id = :sid
              AND event_id = :eid
        """),
        {"tid": tenant_id, "sid": student_id, "eid": new_event_id},
    )
    row = result.mappings().first()
    assert (
        row is not None
    ), "Phase C leave→attendance: No attendance row created by trigger for approved medical leave"
    assert (
        row["status"] == "medical"
    ), f"Phase C leave→attendance: Expected 'medical', got '{row['status']}'"
    assert (
        row["leave_request_id"] == leave_id
    ), "Phase C leave→attendance: leave_request_id not set on auto-materialized attendance"
