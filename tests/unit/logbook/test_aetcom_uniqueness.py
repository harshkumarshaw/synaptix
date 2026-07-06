import uuid

import pytest
from app.schemas.logbook import AetcomReflectionSubmit
from app.services.logbook_service import LogbookService
from sqlalchemy import text


@pytest.mark.anyio
async def test_aetcom_uniqueness_and_cardinality(db_session, tenant_id):
    # Setup dummy student profile
    student_user_id = uuid.uuid4()
    student_id = student_user_id  # In logbook reflection submit, student_id = actor_id

    # Insert student user and profile in DB
    await db_session.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, 'student@jmn.edu', 'Student One', true)"
        ),
        {"id": student_user_id, "t_id": tenant_id},
    )
    # Program
    prog_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-AET', 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id},
    )
    # Academic Year
    ay_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"
        ),
        {"id": ay_id, "t_id": tenant_id},
    )
    # Batch
    batch_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026_A')"
        ),
        {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id},
    )
    # Section
    sect_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO sections (id, tenant_id, batch_id, name) VALUES (:id, :t_id, :b_id, 'Section A')"
        ),
        {"id": sect_id, "t_id": tenant_id, "b_id": batch_id},
    )
    # Student
    await db_session.execute(
        text(
            "INSERT INTO students (id, tenant_id, user_id, batch_id, section_id, roll_number, admission_year, status) VALUES (:id, :t_id, :u_id, :b_id, :s_id, 'ROLL01', 2026, 'active')"
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

    logbook_service = LogbookService(db_session)

    # 1. Submit reflection for Module 1.1, Competency COM-1.1
    sub1 = AetcomReflectionSubmit(
        module_code="Module 1.1",
        competency_code="COM-1.1",
        professional_phase="Phase I",
        reflection_text="First reflection text.",
    )
    r1 = await logbook_service.submit_reflection(
        tenant_id, student_id, sub1, actor_id=student_user_id
    )
    assert r1.id is not None
    assert r1.status == "reflection_submitted"
    assert r1.competency_code == "COM-1.1"

    # 2. Submit reflection for Module 1.1, Competency COM-1.2 (cardinality: multiple competencies per module)
    sub2 = AetcomReflectionSubmit(
        module_code="Module 1.1",
        competency_code="COM-1.2",
        professional_phase="Phase I",
        reflection_text="Second reflection text within same module.",
    )
    r2 = await logbook_service.submit_reflection(
        tenant_id, student_id, sub2, actor_id=student_user_id
    )
    assert r2.id is not None
    assert r2.competency_code == "COM-1.2"
    assert r2.module_code == "Module 1.1"

    # 3. Submit duplicate reflection for Student/Module/Competency/Phase (should fail unique constraint or raise DuplicateRecordError)
    sub3 = AetcomReflectionSubmit(
        module_code="Module 1.1",
        competency_code="COM-1.1",
        professional_phase="Phase I",
        reflection_text="Duplicate reflection attempt.",
    )
    # A fresh submission of the exact same student/module/competency/phase updates it rather than duplicating.
    # Wait, does it? Yes, logbook_service.submit_reflection checks if record exists and updates reflection_text!
    # Let's test that it updates reflection text instead of raising error:
    r3 = await logbook_service.submit_reflection(
        tenant_id, student_id, sub3, actor_id=student_user_id
    )
    assert r3.id == r1.id
    assert r3.reflection_text == "Duplicate reflection attempt."

    # To test the database unique constraint directly, we attempt a direct insert
    # using raw SQL containing duplicate values.
    # This should raise IntegrityError / unique constraint violation.
    with pytest.raises(Exception):
        await db_session.execute(
            text(
                "INSERT INTO aetcom_records (id, tenant_id, student_id, module_code, competency_code, professional_phase, status) "
                "VALUES (:id, :t_id, :stud_id, 'Module 1.1', 'COM-1.1', 'Phase I', 'pending')"
            ),
            {"id": uuid.uuid4(), "t_id": tenant_id, "stud_id": student_id},
        )
        await db_session.commit()
