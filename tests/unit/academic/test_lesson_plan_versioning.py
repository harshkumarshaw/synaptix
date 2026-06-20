import json
import uuid

import pytest
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanUpdate
from app.services.lesson_plan_service import LessonPlanService
from sqlalchemy import text


@pytest.mark.anyio
async def test_lesson_plan_versioning_and_workflow(db_session, tenant_id):
    # Setup dependencies
    dept_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anatomy Dept', 'ANAT_LP')"
        ),
        {"id": dept_id, "t_id": tenant_id},
    )

    prog_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-LP', 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id},
    )

    curr_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-LP')"
        ),
        {"id": curr_id, "t_id": tenant_id, "p_id": prog_id},
    )

    course_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO courses (id, tenant_id, curriculum_id, department_id, name, code, default_attendance_category) VALUES (:id, :t_id, :curr_id, :d_id, 'Anatomy Course', 'ANAT-LP-101', 'theory')"
        ),
        {"id": course_id, "t_id": tenant_id, "curr_id": curr_id, "d_id": dept_id},
    )
    await db_session.commit()

    lp_service = LessonPlanService(db_session)

    # 1. Create a new Lesson Plan (should start as version 1 and status 'draft')
    lp_in = LessonPlanCreate(
        course_id=course_id,
        curriculum_id=curr_id,
        code="AN-1.1",
        topic="Anatomical Terminology",
        description="Introduction to anatomy terminology",
        estimated_hours=1.5,
        competency_code="AN-1.1",
        nmc_competency_level="K",
        is_core=True,
    )

    lp = await lp_service.create_lesson_plan(tenant_id, lp_in)
    assert lp.id is not None
    assert lp.version == 1
    assert lp.is_current is True
    assert lp.status == "draft"

    # 2. Update the lesson plan while in draft status (should update in-place)
    lp_up_1 = LessonPlanUpdate(topic="Updated Anatomical Terminology", estimated_hours=2.0)
    lp_updated = await lp_service.update_lesson_plan(tenant_id, lp.id, lp_up_1)
    assert lp_updated.id == lp.id
    assert lp_updated.version == 1
    assert lp_updated.topic == "Updated Anatomical Terminology"
    assert lp_updated.estimated_hours == 2.0
    assert lp_updated.status == "draft"

    # Seed workflow definition for approval
    wfd_id = uuid.uuid4()
    wfd_steps = {
        "hod_review": {
            "name": "HOD Review",
            "required_role": "HOD",
            "next_steps": ["approved", "rejected"],
        }
    }
    await db_session.execute(
        text(
            "INSERT INTO workflow_definitions (id, tenant_id, name, code, description, version, is_current, steps, is_active) "
            "VALUES (:id, :t_id, 'Lesson Plan Approval Workflow', 'lesson_plan_approval', 'Approve lesson plans', 1, true, :steps, true)"
        ),
        {"id": wfd_id, "t_id": tenant_id, "steps": json.dumps(wfd_steps)},
    )
    await db_session.commit()

    # 3. Submit lesson plan for HOD approval
    lp_submitted = await lp_service.submit_for_approval(tenant_id, lp.id)
    assert lp_submitted.status == "pending_approval"
    assert lp_submitted.workflow_instance_id is not None

    # Check workflow_instances table to see if instance was inserted
    wfi_res = await db_session.execute(
        text(
            "SELECT id, status, current_step, current_assignee_role FROM workflow_instances WHERE id = :id"
        ),
        {"id": lp_submitted.workflow_instance_id},
    )
    wfi = wfi_res.first()
    assert wfi is not None
    assert wfi.status == "pending"
    assert wfi.current_step == "hod_review"
    assert wfi.current_assignee_role == "HOD"

    # 4. Attempting to update a lesson plan in pending_approval should spawn a new version
    lp_up_2 = LessonPlanUpdate(topic="Anatomy Version 2", estimated_hours=2.5)
    new_version_lp = await lp_service.update_lesson_plan(tenant_id, lp.id, lp_up_2)
    assert new_version_lp.id != lp.id
    assert new_version_lp.version == 2
    assert new_version_lp.is_current is True
    assert new_version_lp.status == "draft"
    assert new_version_lp.topic == "Anatomy Version 2"
    assert new_version_lp.estimated_hours == 2.5

    # Check the original lesson plan is no longer current
    orig_lp = await lp_service.get_lesson_plan(tenant_id, lp.id)
    assert orig_lp.is_current is False
    assert orig_lp.status == "pending_approval"
