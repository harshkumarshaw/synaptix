import pytest
import uuid
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowDefinitionCreate, WorkflowStepItem, WorkflowInstanceCreate
from app.models.user import User
from packages.shared.errors import InvalidStateTransitionError, PermissionDeniedError


@pytest.mark.anyio
async def test_workflow_full_lifecycle(db_session, tenant_id, test_user_id):
    """Test a full end-to-end multi-step workflow lifecycle, transitions, history, and constraints.
    
    Manifest IDs: WFL-004, WFL-005, WFL-007, EC-111, EC-112
    """
    
    # Clean up old data to ensure idempotency
    from sqlalchemy import delete
    from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowTransition
    await db_session.execute(delete(WorkflowTransition).where(WorkflowTransition.tenant_id == tenant_id))
    await db_session.execute(delete(WorkflowInstance).where(WorkflowInstance.tenant_id == tenant_id))
    await db_session.execute(
        delete(WorkflowDefinition).where(
            WorkflowDefinition.tenant_id == tenant_id,
            WorkflowDefinition.code == "exemption_approval"
        )
    )
    await db_session.commit()

    # 1. Seed the test user to satisfy actor/assignee FK constraints
    user_exists = await db_session.get(User, test_user_id)
    if not user_exists:
        user = User(
            id=test_user_id,
            tenant_id=tenant_id,
            full_name="Workflow Actor",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

    service = WorkflowService(db_session)

    # 2. Define a multi-stage approval workflow
    # Step flow: draft -> hod_review -> dean_review -> approved / rejected
    definition = await service.create_definition(
        tenant_id,
        WorkflowDefinitionCreate(
            name="Exemption Grant Approval",
            code="exemption_approval",
            steps={
                "draft": WorkflowStepItem(
                    name="draft",
                    required_role="faculty",
                    next_steps=["hod_review"],
                ),
                "hod_review": WorkflowStepItem(
                    name="hod_review",
                    required_role="hod",
                    next_steps=["dean_review", "rejected"],
                ),
                "dean_review": WorkflowStepItem(
                    name="dean_review",
                    required_role="dean",
                    next_steps=["approved", "rejected"],
                ),
            }
        )
    )

    assert definition.code == "exemption_approval"
    assert definition.version == 1

    # 3. Create a workflow instance
    entity_id = uuid.uuid4()
    context = {"exemption_reason": "NMC CBME attendance exemption", "hours": 12}
    instance = await service.create_instance(
        tenant_id,
        WorkflowInstanceCreate(
            definition_code="exemption_approval",
            entity_type="exemption_grant",
            entity_id=entity_id,
            context=context,
            initial_step="draft",
        )
    )

    assert instance.entity_id == entity_id
    assert instance.current_step == "draft"
    assert instance.status == "pending"
    assert instance.current_assignee_role == "faculty"
    assert instance.context == context
    assert len(instance.history) == 0

    # 4. Check active instance limit: Should fail to create another active instance for same entity
    with pytest.raises(Exception):
        await service.create_instance(
            tenant_id,
            WorkflowInstanceCreate(
                definition_code="exemption_approval",
                entity_type="exemption_grant",
                entity_id=entity_id,
                context=context,
                initial_step="draft",
            )
        )

    # 5. Transition 1: draft -> hod_review
    # Actor roles contain 'faculty'
    instance = await service.submit_transition(
        tenant_id=tenant_id,
        instance_id=instance.id,
        to_step="hod_review",
        comment="Submitted for HOD review",
        actor_user_id=test_user_id,
        actor_roles=["faculty"],
    )

    assert instance.current_step == "hod_review"
    assert instance.current_assignee_role == "hod"
    assert instance.status == "pending"

    # 6. Transition 2: Try to bypass dean_review directly to approved (should fail)
    with pytest.raises(InvalidStateTransitionError):
        await service.submit_transition(
            tenant_id=tenant_id,
            instance_id=instance.id,
            to_step="approved",
            comment="Bypass dean",
            actor_user_id=test_user_id,
            actor_roles=["hod"],
        )

    # 7. Transition 3: hod_review -> dean_review
    # Actor roles contain 'hod'
    instance = await service.submit_transition(
        tenant_id=tenant_id,
        instance_id=instance.id,
        to_step="dean_review",
        comment="HOD approved, forwarding to Dean",
        actor_user_id=test_user_id,
        actor_roles=["hod"],
    )

    assert instance.current_step == "dean_review"
    assert instance.current_assignee_role == "dean"
    assert instance.status == "pending"

    # 8. Transition 4: dean_review -> approved (Terminal step)
    # Actor roles contain 'dean'
    instance = await service.submit_transition(
        tenant_id=tenant_id,
        instance_id=instance.id,
        to_step="approved",
        comment="Dean final approval granted",
        actor_user_id=test_user_id,
        actor_roles=["dean"],
    )

    assert instance.current_step == "approved"
    assert instance.status == "approved"
    assert instance.current_assignee_role is None
    assert instance.due_at is None

    # 9. Verify History Array via database reload
    # Refresh instance details from DB
    await db_session.refresh(instance)
    history = instance.history
    assert len(history) == 3

    assert history[0]["from_step"] == "draft"
    assert history[0]["to_step"] == "hod_review"
    assert history[0]["comment"] == "Submitted for HOD review"

    assert history[1]["from_step"] == "hod_review"
    assert history[1]["to_step"] == "dean_review"
    assert history[1]["comment"] == "HOD approved, forwarding to Dean"

    assert history[2]["from_step"] == "dean_review"
    assert history[2]["to_step"] == "approved"
    assert history[2]["comment"] == "Dean final approval granted"
