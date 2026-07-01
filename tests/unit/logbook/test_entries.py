from datetime import date, timedelta
from uuid import uuid4

import pytest
from app.schemas.logbook_phase2 import LogbookEntryCreate, LogbookEntrySubmitRequest
from app.services.logbook_service import LogbookService, LogbookServiceError
from pydantic import ValidationError
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
async def test_log_nmc_006_entry_fields_validation():
    """
    LOG-NMC-006: Logbook entry contains competency_code, level (K/KH/SH/P), is_core.
    """
    data = LogbookEntryCreate(
        student_id=uuid4(),
        subject_code="ANAT",
        professional_phase="Phase I",
        competency_code="AN1.1",
        nmc_level="K",
        is_core=True,
        activity_date=date.today(),
        activity_name="Dissection of Hand",
    )
    assert data.nmc_level == "K"
    assert data.is_core is True

    with pytest.raises(ValidationError):
        LogbookEntryCreate(
            student_id=uuid4(),
            subject_code="ANAT",
            professional_phase="Phase I",
            competency_code="AN1.1",
            nmc_level="INVALID",
            is_core=True,
            activity_date=date.today(),
            activity_name="Dissection of Hand",
        )


@pytest.mark.anyio
async def test_log_nmc_008_student_signoff_initials_required():
    """
    LOG-NMC-008: Student sign-off required (student_initials).
    """
    with pytest.raises(ValidationError):
        LogbookEntrySubmitRequest(student_initials="")


@pytest.mark.anyio
async def test_log_nmc_005_elective_block_entry():
    """
    LOG-NMC-005: Logbook covers Elective Block 1 and Block 2 (Phase III Part I).
    """
    data = LogbookEntryCreate(
        student_id=uuid4(),
        elective_id=uuid4(),
        professional_phase="Phase III Part I",
        competency_code="EL1.1",
        nmc_level="P",
        is_core=False,
        activity_date=date.today(),
        activity_name="Elective Session",
    )
    assert data.elective_id is not None
    assert data.subject_code is None


@pytest.mark.anyio
async def test_log_e004_future_dated_rejected(db_session, tenant_id):
    """
    LOG-E004: Future-dated entry rejected.
    """
    student_id = uuid4()
    await seed_student_profile(db_session, tenant_id, student_id)

    service = LogbookService(db_session)
    future_date = date.today() + timedelta(days=1)

    data = LogbookEntryCreate(
        student_id=student_id,
        subject_code="ANAT",
        professional_phase="Phase I",
        competency_code="AN1.1",
        nmc_level="K",
        is_core=True,
        activity_date=future_date,
        activity_name="Future Dissection",
    )

    with pytest.raises(LogbookServiceError) as exc:
        await service.create_entry(tenant_id, student_id, data)
    assert "Future-dated" in str(exc.value)
