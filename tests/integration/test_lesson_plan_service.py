import pytest
import uuid
import json
from app.services.lesson_plan_service import LessonPlanService
from app.models.lesson_plan import LessonPlan
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanUpdate
from sqlalchemy import text


@pytest.mark.anyio
async def test_lesson_plan_integration_service(db_session, tenant_id):
    # Setup test data
    dept_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Physiology Dept', 'PHYS_LP')"),
        {"id": dept_id, "t_id": tenant_id}
    )
    
    prog_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-LP2', 'professional_phase', 5)"),
        {"id": prog_id, "t_id": tenant_id}
    )
    
    curr_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-LP2')"),
        {"id": curr_id, "t_id": tenant_id, "p_id": prog_id}
    )
    
    course_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO courses (id, tenant_id, curriculum_id, department_id, name, code, default_attendance_category) VALUES (:id, :t_id, :curr_id, :d_id, 'Physiology', 'PHYS-LP-101', 'theory')"),
        {"id": course_id, "t_id": tenant_id, "curr_id": curr_id, "d_id": dept_id}
    )
    await db_session.commit()

    lp_service = LessonPlanService(db_session)

    # 1. Create Lesson Plan
    lp_in = LessonPlanCreate(
        course_id=course_id,
        curriculum_id=curr_id,
        code="PHYS-1.1",
        topic="Cell Physiology",
        description="Introduction to cell membrane functions",
        estimated_hours=2.0,
        competency_code="PHYS-1.1",
        nmc_competency_level="KH",
        is_core=True
    )
    
    lp = await lp_service.create_lesson_plan(tenant_id, lp_in)
    assert lp.id is not None
    assert lp.version == 1
    assert lp.status == "draft"

    # 2. Update Draft Lesson Plan
    lp_up = LessonPlanUpdate(topic="Cell Membrane Physiology", estimated_hours=2.5)
    updated_lp = await lp_service.update_lesson_plan(tenant_id, lp.id, lp_up)
    assert updated_lp.topic == "Cell Membrane Physiology"
    assert updated_lp.estimated_hours == 2.5
    assert updated_lp.version == 1

    # 3. Retrieve Lesson Plan
    fetched_lp = await lp_service.get_lesson_plan(tenant_id, lp.id)
    assert fetched_lp.topic == "Cell Membrane Physiology"
