import datetime
import uuid

import pytest
from app.models.course import Course
from app.models.tenant import Tenant
from app.schemas.calendar import EventCourseBase, EventCreate
from app.services.calendar_service import CalendarService
from sqlalchemy import text


@pytest.mark.anyio
async def test_academic_tenant_isolation(db_session, tenant_id):
    # Tenant A is tenant_id (JMN_TENANT_ID)
    tenant_a = tenant_id
    tenant_b = uuid.UUID("00000000-0000-0000-0000-000000000002")

    # Ensure both tenants exist
    for t_id, code, name in [
        (tenant_a, "JMN", "JMN Medical"),
        (tenant_b, "OTHER", "Other Institution"),
    ]:
        tenant = await db_session.get(Tenant, t_id)
        if not tenant:
            tenant = Tenant(
                id=t_id,
                code=code,
                name=name,
                institution_type="medical",
                regulatory_body="NMC",
            )
            db_session.add(tenant)
    await db_session.commit()

    # Seed courses and academic years for both tenants
    ay_a = uuid.uuid4()
    ay_b = uuid.uuid4()
    prog_a = uuid.uuid4()
    prog_b = uuid.uuid4()
    batch_a = uuid.uuid4()
    batch_b = uuid.uuid4()

    await db_session.execute(
        text(
            "INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, 'AY-A', '2026-08-01', '2027-07-31', true)"
        ),
        {"id": ay_a, "t_id": tenant_a},
    )
    await db_session.execute(
        text(
            "INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, 'AY-B', '2026-08-01', '2027-07-31', true)"
        ),
        {"id": ay_b, "t_id": tenant_b},
    )
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS-A', 'MBBS-A', 'professional_phase', 5)"
        ),
        {"id": prog_a, "t_id": tenant_a},
    )
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS-B', 'MBBS-B', 'professional_phase', 5)"
        ),
        {"id": prog_b, "t_id": tenant_b},
    )
    await db_session.execute(
        text(
            "INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'Batch A', 'BA')"
        ),
        {"id": batch_a, "t_id": tenant_a, "ay_id": ay_a, "prog_id": prog_a},
    )
    await db_session.execute(
        text(
            "INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'Batch B', 'BB')"
        ),
        {"id": batch_b, "t_id": tenant_b, "ay_id": ay_b, "prog_id": prog_b},
    )

    dept_a = uuid.uuid4()
    dept_b = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Dept A', 'DA')"
        ),
        {"id": dept_a, "t_id": tenant_a},
    )
    await db_session.execute(
        text(
            "INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Dept B', 'DB')"
        ),
        {"id": dept_b, "t_id": tenant_b},
    )

    curr_a = uuid.uuid4()
    curr_b = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME A', 'CBME-A')"
        ),
        {"id": curr_a, "t_id": tenant_a, "p_id": prog_a},
    )
    await db_session.execute(
        text(
            "INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME B', 'CBME-B')"
        ),
        {"id": curr_b, "t_id": tenant_b, "p_id": prog_b},
    )

    course_a = Course(
        id=uuid.uuid4(),
        tenant_id=tenant_a,
        curriculum_id=curr_a,
        department_id=dept_a,
        name="Course A",
        code="CA",
        default_attendance_category="theory",
    )
    course_b = Course(
        id=uuid.uuid4(),
        tenant_id=tenant_b,
        curriculum_id=curr_b,
        department_id=dept_b,
        name="Course B",
        code="CB",
        default_attendance_category="theory",
    )
    db_session.add(course_a)
    db_session.add(course_b)
    await db_session.commit()

    # Enable Row Level Security (RLS) mock checks:
    # Set current tenant context parameter in PostgreSQL
    await db_session.execute(text(f"SET LOCAL snx.current_tenant_id = '{tenant_a}'"))

    calendar_service = CalendarService(db_session)

    # 1. Create Event for Tenant A
    event_a_in = EventCreate(
        batch_id=batch_a,
        academic_year_id=ay_a,
        title="Event Tenant A",
        event_type="lecture",
        professional_phase="Phase I",
        date=datetime.date(2026, 9, 10),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        courses=[EventCourseBase(course_id=course_a.id, is_primary=True)],
        assigned_faculty=[],
    )

    event_a = await calendar_service.create_event(tenant_a, event_a_in)
    assert event_a.id is not None
    assert event_a.tenant_id == tenant_a

    # 2. Switch context to Tenant B
    await db_session.execute(text(f"SET LOCAL snx.current_tenant_id = '{tenant_b}'"))

    # Fetching Tenant A's event from Tenant B should return None or raise Error
    # Due to RLS POLICY: USING (tenant_id = current_setting('snx.current_tenant_id')::UUID)
    # The event_a record should be completely hidden from Tenant B
    fetched = await calendar_service.get_event(tenant_b, event_a.id)
    assert fetched is None
