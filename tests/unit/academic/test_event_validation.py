import datetime
import uuid

import pytest
from app.models.course import Course
from app.models.tenant import Tenant
from app.schemas.calendar import EventCourseBase, EventCreate
from app.services.calendar_service import CalendarService


@pytest.mark.anyio
async def test_calendar_event_validations(db_session, tenant_id):
    # Ensure tenant exists
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(
            id=tenant_id,
            code="JMN",
            name="JMN Medical College",
            institution_type="medical",
            regulatory_body="NMC",
        )
        db_session.add(tenant)
        await db_session.commit()

    # Create dummy dependencies
    dept_id = uuid.uuid4()
    # Insert a department using raw sql to avoid missing imports/dependencies
    from sqlalchemy import text

    await db_session.execute(
        text(
            "INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anat', 'AN')"
        ),
        {"id": dept_id, "t_id": tenant_id},
    )

    # Seed program
    prog_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME', 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id},
    )

    # Seed curriculum
    curr_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023')"
        ),
        {"id": curr_id, "t_id": tenant_id, "p_id": prog_id},
    )

    course_id = uuid.uuid4()
    # Create course with default_attendance_category = 'practical'
    course = Course(
        id=course_id,
        tenant_id=tenant_id,
        curriculum_id=curr_id,
        department_id=dept_id,
        name="Anatomy Course",
        code="ANAT-TEST",
        default_attendance_category="practical",
    )
    db_session.add(course)

    batch_id = uuid.uuid4()
    ay_id = uuid.uuid4()
    # Seed academic year
    await db_session.execute(
        text(
            "INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"
        ),
        {"id": ay_id, "t_id": tenant_id},
    )
    # Seed batch
    await db_session.execute(
        text(
            "INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026')"
        ),
        {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id},
    )
    await db_session.commit()

    calendar_service = CalendarService(db_session)

    # 1. Test ECE only in Phase I validation (ECE-NMC-001)
    # Creating ece event in Phase II should fail
    event_in_ece_fail = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="ECE Fail Session",
        event_type="ece",
        professional_phase="Phase II",
        date=datetime.date(2026, 9, 1),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[],
    )
    with pytest.raises(ValueError, match="ECE event type allowed only in Phase I"):
        await calendar_service.create_event(tenant_id, event_in_ece_fail)

    # Creating ece event in Phase I should succeed
    event_in_ece_ok = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="ECE OK Session",
        event_type="ece",
        professional_phase="Phase I",
        date=datetime.date(2026, 9, 1),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[],
    )
    ece_event = await calendar_service.create_event(tenant_id, event_in_ece_ok)
    assert ece_event.id is not None
    # Category should be inherited from Course default ('practical')
    assert ece_event.attendance_category == "practical"

    # 2. Test Clinical Postings not in Phase I validation (ECE-NMC-002)
    event_in_clin_fail = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Clin Fail Session",
        event_type="clinical_posting",
        professional_phase="Phase I",
        date=datetime.date(2026, 9, 15),
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[],
    )
    with pytest.raises(ValueError, match="Clinical postings event type NOT allowed in Phase I"):
        await calendar_service.create_event(tenant_id, event_in_clin_fail)
