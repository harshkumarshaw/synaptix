from datetime import date, timedelta
from uuid import uuid4

import pytest
from app.schemas.logbook_phase2 import LogbookEntryCreate
from app.services.logbook_service import LogbookService
from sqlalchemy import text


async def seed_student_profile(db_session, tenant_id, student_id):
    student_user_id = student_id

    await db_session.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, :email, 'Student One', true)"
        ),
        {"id": student_user_id, "t_id": tenant_id, "email": f"std_{student_id}@jmn.edu"},
    )

    prog_id = uuid4()
    prog_code = f"P-{uuid4().hex[:10]}"
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', :code, 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id, "code": prog_code},
    )

    ay_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"
        ),
        {"id": ay_id, "t_id": tenant_id},
    )

    batch_id = uuid4()
    batch_code = f"B-{uuid4().hex[:10]}"
    await db_session.execute(
        text(
            "INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', :code)"
        ),
        {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id, "code": batch_code},
    )

    sect_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO sections (id, tenant_id, batch_id, name) VALUES (:id, :t_id, :b_id, 'Section A')"
        ),
        {"id": sect_id, "t_id": tenant_id, "b_id": batch_id},
    )

    await db_session.execute(
        text(
            "INSERT INTO students (id, tenant_id, user_id, batch_id, section_id, roll_number, admission_year, status) VALUES (:id, :t_id, :u_id, :b_id, :s_id, 'R01', 2026, 'active')"
        ),
        {
            "id": student_id,
            "t_id": tenant_id,
            "u_id": student_user_id,
            "b_id": batch_id,
            "s_id": sect_id,
        },
    )
    await db_session.commit()


@pytest.mark.anyio
async def test_log_e001_backdated_within_7_days(db_session, tenant_id):
    """
    LOG-E001: Backdated entry within 7 days: accepted without flag.
    """
    student_id = uuid4()
    await seed_student_profile(db_session, tenant_id, student_id)

    service = LogbookService(db_session)
    recent_date = date.today() - timedelta(days=5)

    data = LogbookEntryCreate(
        student_id=student_id,
        subject_code="ANAT",
        professional_phase="Phase I",
        competency_code="AN1.1",
        nmc_level="K",
        activity_date=recent_date,
        activity_name="Recent Activity",
    )

    entry = await service.create_entry(tenant_id, student_id, data)
    assert entry.backdated is False


@pytest.mark.anyio
async def test_log_e002_backdated_8_30_days_flagged(db_session, tenant_id):
    """
    LOG-E002: Backdated entry 8-30 days: accepted but flagged for faculty review.
    """
    student_id = uuid4()
    await seed_student_profile(db_session, tenant_id, student_id)

    service = LogbookService(db_session)
    flagged_date = date.today() - timedelta(days=15)

    data = LogbookEntryCreate(
        student_id=student_id,
        subject_code="ANAT",
        professional_phase="Phase I",
        competency_code="AN1.1",
        nmc_level="K",
        activity_date=flagged_date,
        activity_name="Flagged Activity",
    )

    entry = await service.create_entry(tenant_id, student_id, data)
    assert entry.backdated is True


@pytest.mark.anyio
async def test_log_e003_backdated_over_30_days_hod_review(db_session, tenant_id):
    """
    LOG-E003: Backdated entry >30 days: requires HOD approval.
    """
    student_id = uuid4()
    await seed_student_profile(db_session, tenant_id, student_id)

    service = LogbookService(db_session)
    old_date = date.today() - timedelta(days=45)

    data = LogbookEntryCreate(
        student_id=student_id,
        subject_code="ANAT",
        professional_phase="Phase I",
        competency_code="AN1.1",
        nmc_level="K",
        activity_date=old_date,
        activity_name="Old Activity",
    )

    entry = await service.create_entry(tenant_id, student_id, data)
    assert entry.backdated is True
    assert entry.status == "pending"
    assert entry.backdating_approved_by is None
