from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from app.schemas.logbook_phase2 import (
    LogbookEntryCreate,
    LogbookEntrySubmitRequest,
    LogbookSignoffRequest,
)
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
async def test_log_nmc_013_ia_cap_at_20_percent(db_session, tenant_id):
    """
    LOG-NMC-013: Logbook assessment contributes up to 20% of IA marks.
    Verifies that if configured weight is 25%, the system caps the contribution at 20% of subject max IA marks.
    """
    student_user_id = uuid4()
    student_id = student_user_id
    faculty_user_id = uuid4()

    # Seed student
    await seed_student_profile(db_session, tenant_id, student_id)

    # Seed department and faculty
    dept_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Physiology Dept', 'PHYS')"
        ),
        {"id": dept_id, "t_id": tenant_id},
    )
    await db_session.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, 'f@jmn.edu', 'Faculty', true)"
        ),
        {"id": faculty_user_id, "t_id": tenant_id},
    )
    await db_session.execute(
        text(
            "INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id) VALUES (:id, :t_id, :u_id, :d_id, 'Professor', 'EMP001')"
        ),
        {"id": faculty_user_id, "t_id": tenant_id, "u_id": faculty_user_id, "d_id": dept_id},
    )
    await db_session.commit()

    service = LogbookService(db_session)

    # 1. Create and approve logbook entries
    data = LogbookEntryCreate(
        student_id=student_id,
        subject_code="ANAT",
        professional_phase="Phase I",
        competency_code="AN1.1",
        nmc_level="K",
        activity_date=date.today(),
        activity_name="Dissection",
    )
    entry = await service.create_entry(tenant_id, student_user_id, data)

    # Submit entry
    await service.submit_entry(
        tenant_id, student_id, entry.id, LogbookEntrySubmitRequest(student_initials="SS")
    )

    # Sign off
    await service.signoff_entry(
        tenant_id,
        faculty_user_id,
        entry.id,
        LogbookSignoffRequest(rating="M", faculty_decision="C", faculty_initials="FF"),
    )

    # Recalculate IA with configured weight = 25% (exceeding cap)
    original_get_config = service._get_ia_config

    async def mock_get_ia_config(tenant_id, subject_code, professional_phase):
        return Decimal("25.00"), Decimal("40.00")

    service._get_ia_config = mock_get_ia_config

    await service._recalculate_ia_marks(tenant_id, student_id, "ANAT", "Phase I")

    # Assert
    assessment = await service.get_ia_assessment(tenant_id, student_id, "ANAT", "Phase I")
    assert assessment.ia_marks_pct == Decimal("25.00")
    # Expected: min(100% * 25% * 40, 20% * 40) = min(10, 8) = 8.00
    assert assessment.ia_marks_awarded == Decimal("8.00")


@pytest.mark.anyio
async def test_log_nmc_014_ia_zero_if_incomplete(db_session, tenant_id):
    """
    LOG-NMC-014: Logbook IA contribution is zero if logbook incomplete.
    """
    student_user_id = uuid4()
    student_id = student_user_id

    # Seed student
    await seed_student_profile(db_session, tenant_id, student_id)

    service = LogbookService(db_session)

    # Fetch assessment with no entries
    assessment = await service.get_ia_assessment(tenant_id, student_id, "ANAT", "Phase I")
    assert assessment.total_entries == 0
    assert assessment.completed_entries == 0
    assert assessment.ia_marks_awarded == Decimal("0.00")
    assert assessment.is_complete is False
