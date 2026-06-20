import pytest
from app.models.workflow import WorkflowDefinition
from app.schemas.workflow import WorkflowDefinitionCreate, WorkflowStepItem
from app.services.workflow_service import WorkflowService
from pydantic import ValidationError


@pytest.mark.anyio
async def test_step_json_validation():
    """Verify that step JSON validation rejects definitions with invalid target steps.

    Manifest IDs: WFL-001
    """
    # Valid definition: next steps exist or are terminal
    WorkflowDefinitionCreate(
        name="Leave Approval",
        code="leave_approval",
        steps={
            "start": WorkflowStepItem(
                name="start", required_role="faculty", next_steps=["hod_review"]
            ),
            "hod_review": WorkflowStepItem(
                name="hod_review", required_role="hod", next_steps=["approved", "rejected"]
            ),
        },
    )

    # Invalid definition: target step 'dean_review' does not exist in steps list
    with pytest.raises(ValidationError) as exc:
        WorkflowDefinitionCreate(
            name="Leave Approval",
            code="leave_approval",
            steps={
                "start": WorkflowStepItem(
                    name="start", required_role="faculty", next_steps=["dean_review"]
                ),
            },
        )
    assert "invalid transition target" in str(exc.value)


@pytest.mark.anyio
async def test_definition_versioning_and_immutability(db_session, tenant_id):
    """Test that creating a definition creates a new immutable version and manages is_current flag.

    Manifest IDs: WFL-002, WFL-003, EC-110
    """
    service = WorkflowService(db_session)

    # Clean up any existing definitions with this code
    from sqlalchemy import delete

    await db_session.execute(
        delete(WorkflowDefinition).where(
            WorkflowDefinition.tenant_id == tenant_id,
            WorkflowDefinition.code == "test_version_flow",
        )
    )
    await db_session.commit()

    # Create v1
    def_v1 = await service.create_definition(
        tenant_id,
        WorkflowDefinitionCreate(
            name="V1 Flow",
            code="test_version_flow",
            steps={
                "start": WorkflowStepItem(
                    name="start", required_role="faculty", next_steps=["approved"]
                ),
            },
        ),
    )
    assert def_v1.version == 1
    assert def_v1.is_current is True

    # Create v2 (updates is_current of v1 to False)
    def_v2 = await service.create_definition(
        tenant_id,
        WorkflowDefinitionCreate(
            name="V2 Flow",
            code="test_version_flow",
            steps={
                "start": WorkflowStepItem(
                    name="start", required_role="faculty", next_steps=["approved"]
                ),
            },
        ),
    )
    assert def_v2.version == 2
    assert def_v2.is_current is True

    # Refresh v1 to confirm is_current is now False
    await db_session.refresh(def_v1)
    assert def_v1.is_current is False
