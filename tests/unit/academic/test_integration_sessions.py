import datetime
import uuid

import pytest
from app.models.calendar import Event, EventCourse
from app.models.lesson_plan import LessonPlan
from app.schemas.session import SessionCreate
from app.services.session_tracking_service import SessionTrackingService
from sqlalchemy import text


@pytest.mark.anyio
async def test_session_conducting_and_coverage(db_session, tenant_id):
    # Setup dummy database entries
    dept_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anatomy Dept', 'ANAT_SESS')"
        ),
        {"id": dept_id, "t_id": tenant_id},
    )
    prog_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-SESS', 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id},
    )

    curr_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-SESS')"
        ),
        {"id": curr_id, "t_id": tenant_id, "p_id": prog_id},
    )

    course_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO courses (id, tenant_id, curriculum_id, department_id, name, code, default_attendance_category, subject_code) VALUES (:id, :t_id, :curr_id, :d_id, 'Anatomy', 'ANAT-SESS-101', 'practical', 'ANAT')"
        ),
        {"id": course_id, "t_id": tenant_id, "curr_id": curr_id, "d_id": dept_id},
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
            "INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026_S')"
        ),
        {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id},
    )
    await db_session.commit()

    # Create event
    event_id = uuid.uuid4()
    event = Event(
        id=event_id,
        tenant_id=tenant_id,
        batch_id=batch_id,
        academic_year_id=ay_id,
        title="Session Test Lecture",
        event_type="lecture",
        attendance_category="theory",
        professional_phase="Phase I",
        date=datetime.date(2026, 9, 10),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        status="scheduled",
    )
    db_session.add(event)
    ec = EventCourse(tenant_id=tenant_id, event_id=event_id, course_id=course_id, is_primary=True)
    db_session.add(ec)

    # Create Lesson Plans (1 draft, 2 approved/current)
    lp1_id = uuid.uuid4()
    lp1 = LessonPlan(
        id=lp1_id,
        tenant_id=tenant_id,
        course_id=course_id,
        curriculum_id=curr_id,
        code="AN-LP1",
        version=1,
        is_current=True,
        topic="Topic 1",
        estimated_hours=1.0,
        competency_code="AN-C1",
        nmc_competency_level="K",
        is_core=True,
        status="approved",
    )
    db_session.add(lp1)

    lp2_id = uuid.uuid4()
    lp2 = LessonPlan(
        id=lp2_id,
        tenant_id=tenant_id,
        course_id=course_id,
        curriculum_id=curr_id,
        code="AN-LP2",
        version=1,
        is_current=True,
        topic="Topic 2",
        estimated_hours=2.0,
        competency_code="AN-C2",
        nmc_competency_level="KH",
        is_core=True,
        status="approved",
    )
    db_session.add(lp2)
    await db_session.commit()

    session_service = SessionTrackingService(db_session)

    # 1. Test conducting unplanned session validation (should fail because lesson_plan_id is null and session_reason is empty)
    import pydantic

    with pytest.raises(
        pydantic.ValidationError, match="session_reason is required if lesson_plan_id is null"
    ):
        SessionCreate(
            event_id=event_id,
            lesson_plan_id=None,
            session_reason="",
            conducted_at=datetime.datetime.now(),
            actual_hours=1.0,
            conducted_faculty=[],
        )

    # 2. Conduct a planned session successfully
    sess_in_ok = SessionCreate(
        event_id=event_id,
        lesson_plan_id=lp1_id,
        session_reason=None,
        conducted_at=datetime.datetime.now(),
        actual_hours=1.0,
        conducted_faculty=[],
    )
    session_obj = await session_service.conduct_session(tenant_id, sess_in_ok)
    assert session_obj.id is not None
    assert session_obj.lesson_plan_id == lp1_id
    assert session_obj.actual_hours == 1.0

    # Verify event status is updated to 'conducted'
    updated_event = await db_session.get(Event, event_id)
    assert updated_event.status == "conducted"

    # 3. Verify syllabus coverage calculation (Primary, Topic, and Hours metrics)
    # Total core competencies = 2 (AN-C1, AN-C2)
    # Conducted core competencies = 1 (AN-C1 from lp1)
    # Competency coverage = 1 / 2 = 0.5 (50%)
    # Total topics = 2 (lp1, lp2)
    # Conducted topics = 1 (lp1)
    # Topic coverage = 1 / 2 = 0.5 (50%)
    # Total planned hours = 1.0 (lp1) + 2.0 (lp2) = 3.0
    # Conducted hours = 1.0
    # Hours coverage = 1.0 / 3.0 = 0.3333... (33.3%)
    coverage = await session_service.calculate_syllabus_coverage(tenant_id, course_id, curr_id)
    assert coverage["total_core_competencies"] == 2
    assert coverage["conducted_core_competencies"] == 1
    assert coverage["competency_coverage"] == 0.5

    assert coverage["total_topics"] == 2
    assert coverage["conducted_topics"] == 1
    assert coverage["topic_coverage"] == 0.5

    assert coverage["total_planned_hours"] == 3.0
    assert coverage["conducted_hours"] == 1.0
    assert pytest.approx(coverage["hours_coverage"], 0.01) == 0.333
