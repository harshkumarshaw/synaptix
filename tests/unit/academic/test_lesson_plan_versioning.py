import json
import uuid

import pytest
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanUpdate
from app.services.lesson_plan_service import LessonPlanService
from sqlalchemy import text


@pytest.mark.anyio
async def test_lesson_plan_versioning_and_workflow(db_session, tenant_id):
    """LPN-001, LPN-002, LPN-003: Lesson plan creation, version updates, and submission workflow."""
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
            "INSERT INTO courses (id, tenant_id, curriculum_id, department_id, name, code, default_attendance_category, subject_code) VALUES (:id, :t_id, :curr_id, :d_id, 'Anatomy Course', 'ANAT-LP-101', 'theory', 'ANAT')"
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


@pytest.mark.anyio
async def test_lpn_e001_older_version_retains_conducted_sessions(db_session, tenant_id):
    """LPN-E001: When a lesson plan is versioned, conducted sessions reference the OLD version."""
    from app.services.session_tracking_service import SessionTrackingService
    from app.schemas.session import SessionCreate, SessionFacultyBase
    from app.models.tenant import Tenant
    from app.models.course import Course

    # Setup Tenant
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(id=tenant_id, code="JMN", name="JMN Medical College", institution_type="medical", regulatory_body="NMC")
        db_session.add(tenant)
        await db_session.commit()

    # Setup dependencies
    dept_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anatomy Dept', 'ANAT_LP_E001')"), {"id": dept_id, "t_id": tenant_id})
    prog_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-LP-E001', 'professional_phase', 5)"), {"id": prog_id, "t_id": tenant_id})
    curr_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-LP-E001')"), {"id": curr_id, "t_id": tenant_id, "p_id": prog_id})
    course_id = uuid.uuid4()
    course = Course(id=course_id, tenant_id=tenant_id, curriculum_id=curr_id, department_id=dept_id, name="Anat", code="ANAT-LP-E001", default_attendance_category="theory")
    db_session.add(course)
    ay_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"), {"id": ay_id, "t_id": tenant_id})
    batch_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026-LP-E001')"), {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id})
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

    # Create lesson plan v1
    lp_service = LessonPlanService(db_session)
    lp_in = LessonPlanCreate(
        course_id=course_id,
        curriculum_id=curr_id,
        code="AN-1.1",
        topic="Terminology",
        estimated_hours=2.0,
        competency_code="AN-1.1",
        nmc_competency_level="K",
        is_core=True,
    )
    lp_v1 = await lp_service.create_lesson_plan(tenant_id, lp_in)
    
    # Submit and HOD approved (or just status = pending_approval to trigger versioning on next update)
    lp_v1 = await lp_service.submit_for_approval(tenant_id, lp_v1.id)
    assert lp_v1.status == "pending_approval"

    # Create conducted session referencing v1
    event_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO events (id, tenant_id, batch_id, academic_year_id, title, event_type, attendance_category, professional_phase, date, start_time, end_time, status)
            VALUES (:id, :tenant_id, :batch_id, :academic_year_id, 'Class Terminology', 'lecture', 'theory', 'Phase I', '2026-09-10', '09:00:00', '10:00:00', 'scheduled')
        """),
        {"id": event_id, "tenant_id": tenant_id, "batch_id": batch_id, "academic_year_id": ay_id}
    )
    await db_session.commit()

    tracking_service = SessionTrackingService(db_session)
    session_in = SessionCreate(
        event_id=event_id,
        lesson_plan_id=lp_v1.id,
        actual_hours=2.0,
        conducted_faculty=[]
    )
    conducted_session = await tracking_service.conduct_session(tenant_id, session_in)
    assert conducted_session.lesson_plan_id == lp_v1.id

    # Update lesson plan to spawn version 2
    lp_up = LessonPlanUpdate(topic="Slightly Modified Terminology", estimated_hours=2.0)
    lp_v2 = await lp_service.update_lesson_plan(tenant_id, lp_v1.id, lp_up)
    assert lp_v2.id != lp_v1.id
    assert lp_v2.version == 2
    assert lp_v2.is_current is True

    # Verify that the conducted session still references the old version (v1)
    await db_session.refresh(conducted_session)
    fresh_session = await tracking_service.get_session(tenant_id, conducted_session.id)
    assert fresh_session.lesson_plan_id == lp_v1.id

    # Verify v1 is not deleted
    orig_lp = await lp_service.get_lesson_plan(tenant_id, lp_v1.id)
    assert orig_lp is not None
    assert orig_lp.is_current is False


@pytest.mark.anyio
async def test_lpn_e002_unapproved_plan_compliance_warning(db_session, tenant_id):
    """LPN-E002: Logging a session against an unapproved lesson plan generates compliance warning."""
    from app.services.session_tracking_service import SessionTrackingService
    from app.schemas.session import SessionCreate
    from app.models.tenant import Tenant
    from app.models.course import Course

    # Setup Tenant
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(id=tenant_id, code="JMN", name="JMN Medical College", institution_type="medical", regulatory_body="NMC")
        db_session.add(tenant)
        await db_session.commit()

    # Setup dependencies
    dept_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :t_id, 'Anat Dept', 'ANAT_LP_E002')"), {"id": dept_id, "t_id": tenant_id})
    prog_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-LP-E002', 'professional_phase', 5)"), {"id": prog_id, "t_id": tenant_id})
    curr_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO curricula (id, tenant_id, program_id, name, version_code) VALUES (:id, :t_id, :p_id, 'CBME 2023', 'CBME-2023-LP-E002')"), {"id": curr_id, "t_id": tenant_id, "p_id": prog_id})
    course_id = uuid.uuid4()
    course = Course(id=course_id, tenant_id=tenant_id, curriculum_id=curr_id, department_id=dept_id, name="Anat", code="ANAT-LP-E002", default_attendance_category="theory")
    db_session.add(course)
    ay_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) VALUES (:id, :t_id, '2026-2027', '2026-08-01', '2027-07-31', true)"), {"id": ay_id, "t_id": tenant_id})
    batch_id = uuid.uuid4()
    await db_session.execute(text("INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) VALUES (:id, :t_id, :ay_id, :prog_id, 'MBBS 2026', 'MBBS2026-LP-E002')"), {"id": batch_id, "t_id": tenant_id, "ay_id": ay_id, "prog_id": prog_id})
    await db_session.commit()

    # Create draft (unapproved) lesson plan
    lp_service = LessonPlanService(db_session)
    lp_in = LessonPlanCreate(
        course_id=course_id,
        curriculum_id=curr_id,
        code="AN-1.2",
        topic="Draft Topic",
        estimated_hours=1.0,
        competency_code="AN-1.2",
        nmc_competency_level="K",
        is_core=True,
    )
    lp_v1 = await lp_service.create_lesson_plan(tenant_id, lp_in)
    assert lp_v1.status == "draft"  # Draft is not approved

    # Create event
    event_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO events (id, tenant_id, batch_id, academic_year_id, title, event_type, attendance_category, professional_phase, date, start_time, end_time, status)
            VALUES (:id, :tenant_id, :batch_id, :academic_year_id, 'Class Draft', 'lecture', 'theory', 'Phase I', '2026-09-10', '09:00:00', '10:00:00', 'scheduled')
        """),
        {"id": event_id, "tenant_id": tenant_id, "batch_id": batch_id, "academic_year_id": ay_id}
    )
    await db_session.commit()

    # Log session against draft lesson plan
    tracking_service = SessionTrackingService(db_session)
    session_in = SessionCreate(
        event_id=event_id,
        lesson_plan_id=lp_v1.id,
        actual_hours=1.0,
        conducted_faculty=[]
    )
    actor_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, :email, 'Actor User', true)"),
        {"id": actor_id, "t_id": tenant_id, "email": f"actor_{actor_id}@test.com"}
    )
    await db_session.commit()
    await tracking_service.conduct_session(tenant_id, session_in, actor_id=actor_id)

    # Check that a COMPLIANCE_INCIDENT audit log entry was created
    audit_res = await db_session.execute(
        text("SELECT action, resource_type, new_values FROM audit_log WHERE tenant_id = :tid AND action = 'COMPLIANCE_INCIDENT'"),
        {"tid": tenant_id}
    )
    audit_row = audit_res.first()
    assert audit_row is not None
    assert audit_row.action == "COMPLIANCE_INCIDENT"
    assert audit_row.resource_type == "session"
    assert "unapproved_lesson_plan_session" in audit_row.new_values["incident_type"]

