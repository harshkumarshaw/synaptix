import pytest
import uuid
import packages.shared.db.session as db_session_mod
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowDefinitionCreate, WorkflowStepItem, WorkflowInstanceCreate
from app.models.tenant import Tenant
from app.models.user import User
from packages.shared.errors import ResourceNotFoundError


@pytest.mark.anyio
async def test_tenant_isolation_rls(db_session, tenant_id, test_user_id):
    """Test that database Row Level Security (RLS) restricts access across tenants.
    
    Manifest IDs: WFL-006, EC-113, TNT-002, TNT-003, TNT-004, AUD-002, AUD-003
    """
    # 1. Create a second tenant B
    tenant_b_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    
    tenant_b_exists = await db_session.get(Tenant, tenant_b_id)
    if not tenant_b_exists:
        tenant_b = Tenant(
            id=tenant_b_id,
            name="Second Tenant",
            code="TENANT_B",
            institution_type="medical",
            regulatory_body="nmc",
        )
        db_session.add(tenant_b)
        await db_session.commit()

    # Create actor for Tenant A
    user_a = await db_session.get(User, test_user_id)
    if not user_a:
        user_a = User(id=test_user_id, tenant_id=tenant_id, full_name="User A", is_active=True)
        db_session.add(user_a)
        await db_session.commit()

    # Create actor for Tenant B
    test_user_b_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    user_b = await db_session.get(User, test_user_b_id)
    if not user_b:
        user_b = User(id=test_user_b_id, tenant_id=tenant_b_id, full_name="User B", is_active=True)
        db_session.add(user_b)
        await db_session.commit()

    service = WorkflowService(db_session)

    # 2. Add Definition under Tenant A context
    await db_session_mod.set_tenant_context(db_session, tenant_id)
    def_a = await service.create_definition(
        tenant_id,
        WorkflowDefinitionCreate(
            name="Workflow A",
            code="workflow_shared_code",
            steps={"start": WorkflowStepItem(name="start", required_role="faculty", next_steps=["approved"])}
        )
    )

    # Create instance A
    inst_a = await service.create_instance(
        tenant_id,
        WorkflowInstanceCreate(
            definition_code="workflow_shared_code",
            entity_type="leave_request",
            entity_id=uuid.uuid4(),
            initial_step="start",
            context={},
        )
    )

    # 3. Switch context to Tenant B and create Definition & Instance with same code
    await db_session_mod.set_tenant_context(db_session, tenant_b_id)
    def_b = await service.create_definition(
        tenant_b_id,
        WorkflowDefinitionCreate(
            name="Workflow B",
            code="workflow_shared_code",
            steps={"start": WorkflowStepItem(name="start", required_role="faculty", next_steps=["approved"])}
        )
    )

    inst_b = await service.create_instance(
        tenant_b_id,
        WorkflowInstanceCreate(
            definition_code="workflow_shared_code",
            entity_type="leave_request",
            entity_id=uuid.uuid4(),
            initial_step="start",
            context={},
        )
    )

    # 4. Under Tenant B context, query definition by Tenant A's ID. Should fail.
    with pytest.raises(ResourceNotFoundError):
        await service.get_definition(tenant_b_id, def_a.id)

    # Under Tenant B context, query instance by Tenant A's ID. Should fail.
    with pytest.raises(ResourceNotFoundError):
        await service.get_instance(tenant_b_id, inst_a.id)

    # Under Tenant B context, try to transition Tenant A's instance. Should fail.
    with pytest.raises(ResourceNotFoundError):
        await service.submit_transition(
            tenant_id=tenant_b_id,
            instance_id=inst_a.id,
            to_step="approved",
            comment="illegal bypass",
            actor_user_id=test_user_b_id,
            actor_roles=["faculty"],
        )

    # 5. Switch back to Tenant A context
    await db_session_mod.set_tenant_context(db_session, tenant_id)

    # Query definition by Tenant B's ID. Should fail.
    with pytest.raises(ResourceNotFoundError):
        await service.get_definition(tenant_id, def_b.id)

    # Query instance by Tenant B's ID. Should fail.
    with pytest.raises(ResourceNotFoundError):
        await service.get_instance(tenant_id, inst_b.id)
