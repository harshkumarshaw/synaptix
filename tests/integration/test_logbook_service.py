import pytest
import uuid
import datetime
from app.services.logbook_service import LogbookService
from app.schemas.logbook import (
    FoundationCourseHoursLog,
    FoundationCourseSignoffPayload,
    AetcomReflectionSubmit,
    AetcomSignoffPayload,
)
from sqlalchemy import text


@pytest.mark.anyio
async def test_logbook_service_flows(db_session, tenant_id):
    # Setup student and faculty profiles in DB
    student_user_id = uuid.uuid4()
    student_id = student_user_id
    
    faculty_user_id = uuid.uuid4()
    faculty_id = faculty_user_id

    # Seed academic structures
    await db_session.execute(
        text("INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, 'student@jmn.edu', 'Student One', true)"),
        {"id": student_user_id, "t_id": tenant_id}
    )
    await db_session.execute(
        text("INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, 'fac@jmn.edu', 'Faculty User', true)"),
        {"id": faculty_user_id, "t_id": tenant_id}
    )
    
    dept_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Physiology Dept', 'PHYS_LOG')"),
        {"id": dept_id, "t_id": tenant_id}
    )
    
    # Program
    prog_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-LOG', 'professional_phase', 5)"),
        {"id": prog_id, "t_id": tenant_id}
    )
    
    # Academic Year
    ay_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"),
        {"id": ay_id, "t_id": tenant_id}
    )
    
    # Batch
    batch_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026_L')"),
        {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id}
    )
    
    # Section
    sect_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO sections (id, tenant_id, batch_id, name) VALUES (:id, :t_id, :b_id, 'Section A')"),
        {"id": sect_id, "t_id": tenant_id, "b_id": batch_id}
    )

    # Profiles
    await db_session.execute(
        text("INSERT INTO students (id, tenant_id, user_id, batch_id, section_id, roll_number, admission_year, status) VALUES (:id, :t_id, :u_id, :b_id, :s_id, 'ROLL01', 2026, 'active')"),
        {"id": student_id, "t_id": tenant_id, "u_id": student_user_id, "b_id": batch_id, "s_id": sect_id}
    )
    await db_session.execute(
        text("INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id) VALUES (:id, :t_id, :u_id, :d_id, 'Prof', 'EMP-01')"),
        {"id": faculty_id, "t_id": tenant_id, "u_id": faculty_user_id, "d_id": dept_id}
    )
    await db_session.commit()

    logbook_service = LogbookService(db_session)

    # 1. Foundation Course hours tracking
    # Default required hours for 'hospital_visits' is 10.0. Log 5.0 hours.
    h_log = FoundationCourseHoursLog(
        student_id=student_id,
        module_name="hospital_visits",
        hours=5.0
    )
    
    r1 = await logbook_service.log_foundation_hours(tenant_id, h_log, actor_id=student_user_id)
    assert r1.completed_hours == 5.0
    assert r1.is_completed is False
    assert r1.required_hours == 10.0

    # Log 6.0 hours more (should exceed 10.0 and mark completed)
    h_log_2 = FoundationCourseHoursLog(
        student_id=student_id,
        module_name="hospital_visits",
        hours=6.0
    )
    r2 = await logbook_service.log_foundation_hours(tenant_id, h_log_2, actor_id=student_user_id)
    assert r2.completed_hours == 11.0
    assert r2.is_completed is True

    # 2. Foundation Course module sign-off
    so_payload = FoundationCourseSignoffPayload(
        student_id=student_id,
        module_name="orientation"
    )
    r3 = await logbook_service.signoff_foundation_module(tenant_id, so_payload, signed_off_by=faculty_id)
    assert r3.is_completed is True
    assert r3.signed_off_by == faculty_id
    assert r3.signoff_received_at is not None

    # Retrieve progress list
    progress = await logbook_service.get_student_foundation_progress(tenant_id, student_id)
    assert len(progress) == 2

    # 3. AETCOM reflection submit & signoff
    aet_submit = AetcomReflectionSubmit(
        module_code="Module 1.2",
        competency_code="COM-1.2",
        professional_phase="Phase I",
        reflection_text="Personal reflection."
    )
    aet_rec = await logbook_service.submit_reflection(tenant_id, student_id, aet_submit, actor_id=student_user_id)
    assert aet_rec.status == "reflection_submitted"
    assert aet_rec.reflection_text == "Personal reflection."

    # AETCOM sign-off
    aet_so = AetcomSignoffPayload(
        student_id=student_id,
        module_code="Module 1.2",
        competency_code="COM-1.2",
        professional_phase="Phase I"
    )
    aet_signed = await logbook_service.signoff_aetcom_competency(tenant_id, aet_so, signed_off_by=faculty_id)
    assert aet_signed.status == "completed"
    assert aet_signed.signed_off_by == faculty_id
    assert aet_signed.signed_off_at is not None

    # Retrieve aetcom list
    aetcoms = await logbook_service.get_student_aetcom_records(tenant_id, student_id)
    assert len(aetcoms) == 1
    assert aetcoms[0].status == "completed"
