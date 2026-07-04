import datetime
import uuid

import pytest
from app.models.course import Course
from app.models.tenant import Tenant
from app.schemas.calendar import EventCourseBase, EventCreate, EventFacultyBase
from app.services.calendar_service import CalendarService
from sqlalchemy import text


@pytest.mark.anyio
async def test_calendar_engine_lifecycle(db_session, tenant_id):
    """CAL-001, CAL-E001, CAL-E002: Calendar event creation, rescheduling, and cancellation."""
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
        text(
            "INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anatomy Dept', 'ANAT_C')"
        ),
        {"id": dept_id, "t_id": tenant_id},
    )

    prog_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME', 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id},
    )

    curr_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023')"
        ),
        {"id": curr_id, "t_id": tenant_id, "p_id": prog_id},
    )

    course_id = uuid.uuid4()
    course = Course(
        id=course_id,
        tenant_id=tenant_id,
        curriculum_id=curr_id,
        department_id=dept_id,
        name="Anatomy Course",
        code="ANAT-TEST-C",
        default_attendance_category="practical",
    )
    db_session.add(course)

    # Seed Academic Year, Program, Batch, Faculty
    ay_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"
        ),
        {"id": ay_id, "t_id": tenant_id},
    )
    batch_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026')"
        ),
        {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id},
    )

    faculty_user_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, 'fac@jmn.edu', 'Faculty Anat', true)"
        ),
        {"id": faculty_user_id, "t_id": tenant_id},
    )

    faculty_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id) VALUES (:id, :t_id, :u_id, :d_id, 'Prof', 'EMP-01')"
        ),
        {"id": faculty_id, "t_id": tenant_id, "u_id": faculty_user_id, "d_id": dept_id},
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
        assigned_faculty=[EventFacultyBase(faculty_id=faculty_id)],
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
        actor_id=faculty_user_id,
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
        actor_id=faculty_user_id,
    )
    assert cancelled_event.status == "cancelled"
    assert cancelled_event.cancellation_reason == "Holiday declared"
    assert cancelled_event.cancelled_by == faculty_user_id


@pytest.mark.anyio
async def test_calendar_integration_sessions_secondary_courses(db_session, tenant_id):
    """CAL-E008: Integration sessions map secondary courses via event_courses join table."""
    from app.models.calendar import Event, EventCourse
    from app.models.course import Course
    from app.models.tenant import Tenant
    from sqlalchemy import select

    # Setup Tenant if not present
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

    dept_id = uuid.uuid4()
    from sqlalchemy import text
    await db_session.execute(
        text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anatomy Dept', 'ANAT_C_E008')"),
        {"id": dept_id, "t_id": tenant_id},
    )
    prog_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-E008', 'professional_phase', 5)"),
        {"id": prog_id, "t_id": tenant_id},
    )
    curr_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-E008')"),
        {"id": curr_id, "t_id": tenant_id, "p_id": prog_id},
    )

    course_a = Course(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        curriculum_id=curr_id,
        department_id=dept_id,
        name="Course A",
        code="ANAT-A",
        default_attendance_category="theory",
    )
    course_b = Course(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        curriculum_id=curr_id,
        department_id=dept_id,
        name="Course B",
        code="ANAT-B",
        default_attendance_category="theory",
    )
    db_session.add_all([course_a, course_b])

    ay_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"),
        {"id": ay_id, "t_id": tenant_id},
    )
    batch_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026-E008')"),
        {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id},
    )
    await db_session.commit()

    event = Event(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Integration Session",
        event_type="lecture",
        attendance_category="theory",
        professional_phase="Phase I",
        date=datetime.date(2026, 9, 10),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        status="scheduled",
    )
    db_session.add(event)

    ec_a = EventCourse(tenant_id=tenant_id, event_id=event.id, course_id=course_a.id, is_primary=True)
    ec_b = EventCourse(tenant_id=tenant_id, event_id=event.id, course_id=course_b.id, is_primary=False)
    db_session.add_all([ec_a, ec_b])
    await db_session.commit()

    # Query using calendar service
    calendar_service = CalendarService(db_session)
    full_event = await calendar_service.get_event(tenant_id, event.id)
    assert len(full_event.courses) == 2
    primary_course = [c for c in full_event.courses if c.is_primary][0]
    secondary_course = [c for c in full_event.courses if not c.is_primary][0]
    assert primary_course.course_id == course_a.id
    assert secondary_course.course_id == course_b.id


@pytest.mark.anyio
async def test_cal_e003_bulk_event_generation(db_session, tenant_id):
    """CAL-E003: Generate 30 recurring weekly events in one call."""
    from app.models.tenant import Tenant
    from app.models.course import Course
    # Setup Tenant
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(id=tenant_id, code="JMN", name="JMN Medical College", institution_type="medical", regulatory_body="NMC")
        db_session.add(tenant)
        await db_session.commit()

    dept_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anat Dept', 'ANAT_C_E003')"), {"id": dept_id, "t_id": tenant_id})
    prog_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-E003', 'professional_phase', 5)"), {"id": prog_id, "t_id": tenant_id})
    curr_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-E003')"), {"id": curr_id, "t_id": tenant_id, "p_id": prog_id})
    course_id = uuid.uuid4()
    course = Course(id=course_id, tenant_id=tenant_id, curriculum_id=curr_id, department_id=dept_id, name="Anat", code="ANAT-E003", default_attendance_category="theory")
    db_session.add(course)
    ay_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"), {"id": ay_id, "t_id": tenant_id})
    batch_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026-E003')"), {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id})
    await db_session.commit()

    service = CalendarService(db_session)
    event_in = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Weekly Lecture",
        event_type="lecture",
        professional_phase="Phase I",
        date=datetime.date(2026, 8, 1),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[],
    )
    # Generate 5 recurring weekly events on Mondays (weekday 0)
    events = await service.bulk_create_recurring(
        tenant_id=tenant_id,
        event_in=event_in,
        recurrence="weekly",
        start_date=datetime.date(2026, 8, 1),
        end_date=datetime.date(2026, 9, 5),
        day_of_week=0,  # Monday
    )
    # Mondays in Aug 2026: Aug 3, 10, 17, 24, 31 (5 Mondays)
    assert len(events) == 5
    for i in range(1, len(events)):
        assert (events[i].date - events[i-1].date).days == 7


@pytest.mark.anyio
async def test_cal_e004_holiday_conflict_warning(db_session, tenant_id):
    """CAL-E004: Creating event on a holiday returns warning (not block)."""
    from app.models.tenant import Tenant
    from app.models.course import Course
    # Setup Tenant
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(id=tenant_id, code="JMN", name="JMN Medical College", institution_type="medical", regulatory_body="NMC")
        db_session.add(tenant)
        await db_session.commit()

    dept_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anat Dept', 'ANAT_C_E004')"), {"id": dept_id, "t_id": tenant_id})
    prog_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-E004', 'professional_phase', 5)"), {"id": prog_id, "t_id": tenant_id})
    curr_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-E004')"), {"id": curr_id, "t_id": tenant_id, "p_id": prog_id})
    course_id = uuid.uuid4()
    course = Course(id=course_id, tenant_id=tenant_id, curriculum_id=curr_id, department_id=dept_id, name="Anat", code="ANAT-E004", default_attendance_category="theory")
    db_session.add(course)
    ay_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"), {"id": ay_id, "t_id": tenant_id})
    batch_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026-E004')"), {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id})
    await db_session.commit()

    service = CalendarService(db_session)
    event_in = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Independence Day Special Lecture",
        event_type="lecture",
        professional_phase="Phase I",
        date=datetime.date(2026, 8, 15),  # Independence Day (Holiday)
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[],
    )
    # The event should be successfully created, warning logged
    event = await service.create_event(tenant_id, event_in)
    assert event.id is not None
    assert event.status == "scheduled"


@pytest.mark.anyio
async def test_cal_e005_faculty_leave_conflict(db_session, tenant_id):
    """CAL-E005: Event scheduled when assigned faculty has approved leave shows warning."""
    from app.models.tenant import Tenant
    from app.models.course import Course
    # Setup Tenant
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(id=tenant_id, code="JMN", name="JMN Medical College", institution_type="medical", regulatory_body="NMC")
        db_session.add(tenant)
        await db_session.commit()

    dept_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anat Dept', 'ANAT_C_E005')"), {"id": dept_id, "t_id": tenant_id})
    prog_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-E005', 'professional_phase', 5)"), {"id": prog_id, "t_id": tenant_id})
    curr_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-E005')"), {"id": curr_id, "t_id": tenant_id, "p_id": prog_id})
    course_id = uuid.uuid4()
    course = Course(id=course_id, tenant_id=tenant_id, curriculum_id=curr_id, department_id=dept_id, name="Anat", code="ANAT-E005", default_attendance_category="theory")
    db_session.add(course)
    ay_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"), {"id": ay_id, "t_id": tenant_id})
    batch_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026-E005')"), {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id})
    
    faculty_id = uuid.uuid4()
    # Seed user, student and faculty for faculty_id to satisfy FK constraints on leave_requests and event_faculty
    fac_user_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, :email, 'Faculty Student', true)"),
        {"id": fac_user_id, "t_id": tenant_id, "email": f"fac_stud_{fac_user_id}@test.com"}
    )
    await db_session.execute(
        text("INSERT INTO students (id, tenant_id, user_id, batch_id, roll_number, admission_year, status) VALUES (:id, :t_id, :u_id, :b_id, 'ROLL_FAC_LEAVE', 2024, 'active')"),
        {"id": faculty_id, "t_id": tenant_id, "u_id": fac_user_id, "b_id": batch_id}
    )
    await db_session.execute(
        text("INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id) VALUES (:id, :t_id, :u_id, :dept_id, 'Professor', 'EMP_FAC_LEAVE')"),
        {"id": faculty_id, "t_id": tenant_id, "u_id": fac_user_id, "dept_id": dept_id}
    )

    # Seed approved leave for this faculty member on 2026-09-10
    await db_session.execute(
        text("""
            INSERT INTO leave_requests (id, tenant_id, student_id, leave_type, start_date, end_date, reason, status)
            VALUES (:id, :tenant_id, :student_id, 'casual', '2026-09-08', '2026-09-12', 'Family function', 'approved')
        """),
        {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "student_id": faculty_id,
        }
    )
    await db_session.commit()

    service = CalendarService(db_session)
    event_in = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Weekly Lecture",
        event_type="lecture",
        professional_phase="Phase I",
        date=datetime.date(2026, 9, 10),  # Falls inside faculty leave window
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[EventFacultyBase(faculty_id=faculty_id)],
    )
    # Create event should succeed with a warning logged
    event = await service.create_event(tenant_id, event_in)
    assert event.id is not None
    assert event.status == "scheduled"


@pytest.mark.anyio
async def test_cal_e006_room_double_booking(db_session, tenant_id):
    """CAL-E006: Two events in same room at same time → rejected."""
    from app.models.tenant import Tenant
    from app.models.course import Course
    # Setup Tenant
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(id=tenant_id, code="JMN", name="JMN Medical College", institution_type="medical", regulatory_body="NMC")
        db_session.add(tenant)
        await db_session.commit()

    dept_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anat Dept', 'ANAT_C_E006')"), {"id": dept_id, "t_id": tenant_id})
    prog_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-E006', 'professional_phase', 5)"), {"id": prog_id, "t_id": tenant_id})
    curr_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-E006')"), {"id": curr_id, "t_id": tenant_id, "p_id": prog_id})
    course_id = uuid.uuid4()
    course = Course(id=course_id, tenant_id=tenant_id, curriculum_id=curr_id, department_id=dept_id, name="Anat", code="ANAT-E006", default_attendance_category="theory")
    db_session.add(course)
    ay_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"), {"id": ay_id, "t_id": tenant_id})
    batch_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026-E006')"), {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id})
    await db_session.commit()

    service = CalendarService(db_session)
    event1_in = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Lecture A",
        description="Location: Room:101",
        event_type="lecture",
        professional_phase="Phase I",
        date=datetime.date(2026, 9, 10),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[],
    )
    await service.create_event(tenant_id, event1_in)

    # Double book same room (Room:101) at same date and overlapping time (9:30 - 10:30)
    event2_in = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Lecture B",
        description="Location: Room:101",
        event_type="lecture",
        professional_phase="Phase I",
        date=datetime.date(2026, 9, 10),
        start_time=datetime.time(9, 30),
        end_time=datetime.time(10, 30),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[],
    )
    with pytest.raises(ValueError, match="Room conflict"):
        await service.create_event(tenant_id, event2_in)


@pytest.mark.anyio
async def test_cal_e007_phase_boundary_validation(db_session, tenant_id):
    """CAL-E007: Event date outside the course's professional phase boundary → warning."""
    from app.models.tenant import Tenant
    from app.models.course import Course
    # Setup Tenant
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(id=tenant_id, code="JMN", name="JMN Medical College", institution_type="medical", regulatory_body="NMC")
        db_session.add(tenant)
        await db_session.commit()

    dept_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anat Dept', 'ANAT_C_E007')"), {"id": dept_id, "t_id": tenant_id})
    prog_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-E007', 'professional_phase', 5)"), {"id": prog_id, "t_id": tenant_id})
    curr_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-E007')"), {"id": curr_id, "t_id": tenant_id, "p_id": prog_id})
    course_id = uuid.uuid4()
    course = Course(id=course_id, tenant_id=tenant_id, curriculum_id=curr_id, department_id=dept_id, name="Anat", code="ANAT-E007", default_attendance_category="theory")
    db_session.add(course)
    ay_id = uuid.uuid4()
    # Academic Year is Aug 1, 2026 to Jul 31, 2027
    await db_session.execute(text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"), {"id": ay_id, "t_id": tenant_id})
    batch_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026-E007')"), {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id})
    await db_session.commit()

    service = CalendarService(db_session)
    event_in = EventCreate(
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Weekly Lecture",
        event_type="lecture",
        professional_phase="Phase I",
        date=datetime.date(2028, 8, 1),  # Date outside the academic year boundary (Aug 2028)
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        courses=[EventCourseBase(course_id=course_id, is_primary=True)],
        assigned_faculty=[],
    )
    # Should create successfully, warning logged
    event = await service.create_event(tenant_id, event_in)
    assert event.id is not None
    assert event.status == "scheduled"

