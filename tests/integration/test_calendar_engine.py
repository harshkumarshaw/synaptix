import pytest
import datetime
import uuid
from app.services.calendar_service import CalendarService
from app.models.course import Course
from app.models.tenant import Tenant
from app.schemas.calendar import EventCreate, EventCourseBase, EventFacultyBase
from sqlalchemy import text


@pytest.mark.anyio
async def test_calendar_engine_lifecycle(db_session, tenant_id):
    # Setup JMN Tenant if not present
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
    await db_session.execute(
        text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anatomy Dept', 'ANAT_C')"),
        {"id": dept_id, "t_id": tenant_id}
    )

    prog_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME', 'professional_phase', 5)"),
        {"id": prog_id, "t_id": tenant_id}
    )
    
    curr_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023')"),
        {"id": curr_id, "t_id": tenant_id, "p_id": prog_id}
    )

    course_id = uuid.uuid4()
    course = Course(
        id=course_id,
        tenant_id=tenant_id,
        curriculum_id=curr_id,
        department_id=dept_id,
        name="Anatomy Course",
        code="ANAT-TEST-C",
        default_attendance_category="practical"
    )
    db_session.add(course)

    # Seed Academic Year, Program, Batch, Faculty
    ay_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"),
        {"id": ay_id, "t_id": tenant_id}
    )
    batch_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026')"),
        {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id}
    )

    faculty_user_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, 'fac@jmn.edu', 'Faculty Anat', true)"),
        {"id": faculty_user_id, "t_id": tenant_id}
    )

    faculty_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id) VALUES (:id, :t_id, :u_id, :d_id, 'Prof', 'EMP-01')"),
        {"id": faculty_id, "t_id": tenant_id, "u_id": faculty_user_id, "d_id": dept_id}
    )
    await db_session.commit()

    calendar_service = CalendarService(db_session)

    # 1. Create Event
    event_in = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Anatomy Practical Class",
        event_type="practical",
        professional_phase="Phase I",
        date=datetime.date(2026, 9, 10),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(11, 0),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[EventFacultyBase(faculty_id=faculty_id)]
    )

    event = await calendar_service.create_event(tenant_id, event_in, actor_id=faculty_user_id)
    assert event.id is not None
    assert event.status == "scheduled"
    assert event.attendance_category == "practical"

    # Fetch event with relations
    full_event = await calendar_service.get_event(tenant_id, event.id)
    assert len(full_event.courses) == 1
    assert full_event.courses[0].course_id == course_id
    assert full_event.courses[0].is_primary is True
    assert len(full_event.assigned_faculty) == 1
    assert full_event.assigned_faculty[0].faculty_id == faculty_id

    # 2. Reschedule Event
    new_date = datetime.date(2026, 9, 11)
    new_start = datetime.time(10, 0)
    new_end = datetime.time(12, 0)
    
    new_event = await calendar_service.reschedule_event(
        tenant_id=tenant_id,
        event_id=event.id,
        new_date=new_date,
        new_start=new_start,
        new_end=new_end,
        actor_id=faculty_user_id
    )
    
    # Original event should now be status='rescheduled'
    orig_event = await calendar_service.get_event(tenant_id, event.id)
    assert orig_event.status == "rescheduled"

    # New event should be status='scheduled' and point to parent_event_id
    assert new_event.id != event.id
    assert new_event.status == "scheduled"
    assert new_event.parent_event_id == event.id
    assert new_event.date == new_date
    assert new_event.start_time == new_start
    assert new_event.end_time == new_end

    # Check relation mappings are copied
    full_new_event = await calendar_service.get_event(tenant_id, new_event.id)
    assert len(full_new_event.courses) == 1
    assert full_new_event.courses[0].course_id == course_id
    assert len(full_new_event.assigned_faculty) == 1

    # 3. Cancel Rescheduled Event
    cancelled_event = await calendar_service.cancel_event(
        tenant_id=tenant_id,
        event_id=new_event.id,
        reason="Holiday declared",
        actor_id=faculty_user_id
    )
    assert cancelled_event.status == "cancelled"
    assert cancelled_event.cancellation_reason == "Holiday declared"
    assert cancelled_event.cancelled_by == faculty_user_id
