import pytest
import uuid
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowDefinitionCreate, WorkflowStepItem, WorkflowInstanceCreate
from packages.shared.errors import InvalidStateTransitionError, PermissionDeniedError
from app.models.user import User


@pytest.mark.anyio
async def test_workflow_transitions_validation(db_session, tenant_id, test_user_id):
    """Test transitions validation rules: next steps allowed and actor roles check.
    
    Manifest IDs: WFL-005, WFL-008
    """
    # Clean up old data
    from sqlalchemy import delete
    from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowTransition
    await db_session.execute(delete(WorkflowTransition).where(WorkflowTransition.tenant_id == tenant_id))
    await db_session.execute(delete(WorkflowInstance).where(WorkflowInstance.tenant_id == tenant_id))
    await db_session.execute(
        delete(WorkflowDefinition).where(
            WorkflowDefinition.tenant_id == tenant_id,
            WorkflowDefinition.code == "test_transitions"
        )
    )
    await db_session.commit()

    # Seed User record to satisfy audit log FK constraints
    user_exists = await db_session.get(User, test_user_id)
    if not user_exists:
        user = User(
            id=test_user_id,
            tenant_id=tenant_id,
            full_name="Test Actor",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

    service = WorkflowService(db_session)


    # 1. Create a test definition
    definition = await service.create_definition(
        tenant_id,
        WorkflowDefinitionCreate(
            name="Testing Transitions",
            code="test_transitions",
            steps={
                "start": WorkflowStepItem(name="start", required_role="faculty", next_steps=["hod_review"]),
                "hod_review": WorkflowStepItem(name="hod_review", required_role="hod", next_steps=["approved", "rejected"]),
            }
        )
    )

    # 2. Create instance
    instance = await service.create_instance(
        tenant_id,
        WorkflowInstanceCreate(
            definition_code="test_transitions",
            entity_type="leave_request",
            entity_id=uuid.uuid4(),
            context={"reason": "sick"},
            initial_step="start",
        )
    )
    assert instance.current_step == "start"
    assert instance.status == "pending"

    # ── Test A: Invalid next step (start cannot go directly to approved) ──
    with pytest.raises(InvalidStateTransitionError):
        await service.submit_transition(
            tenant_id=tenant_id,
            instance_id=instance.id,
            to_step="approved",
            comment="skip hod",
            actor_user_id=test_user_id,
            actor_roles=["faculty"],
        )

    # ── Test B: Lack of required role (acting on start step requires 'faculty' role) ──
    with pytest.raises(PermissionDeniedError):
        await service.submit_transition(
            tenant_id=tenant_id,
            instance_id=instance.id,
            to_step="hod_review",
            comment="submit",
            actor_user_id=test_user_id,
            actor_roles=["student"],  # student lacks faculty role
        )

    # ── Test C: Valid transition (faculty role can submit to hod_review) ──
    instance = await service.submit_transition(
        tenant_id=tenant_id,
        instance_id=instance.id,
        to_step="hod_review",
        comment="submit",
        actor_user_id=test_user_id,
        actor_roles=["faculty"],
    )
    assert instance.current_step == "hod_review"
    assert instance.status == "pending"
    assert instance.current_assignee_role == "hod"

    # ── Test D: Valid terminal transition (hod role can reject) ──
    instance = await service.submit_transition(
        tenant_id=tenant_id,
        instance_id=instance.id,
        to_step="rejected",
        comment="no way",
        actor_user_id=test_user_id,
        actor_roles=["hod"],
    )
    assert instance.current_step == "rejected"
    assert instance.status == "rejected"
    assert instance.current_assignee_role is None
