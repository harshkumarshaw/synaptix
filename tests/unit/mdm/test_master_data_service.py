import pytest
import uuid
from app.services.master_data_service import MasterDataService
from app.schemas.master_data import MasterDataEntityCreate, MasterDataEntityUpdate
from packages.shared.errors import ResourceNotFoundError, DuplicateRecordError


@pytest.mark.anyio
async def test_mdm_lifecycle(db_session, tenant_id):
    """Test creation, retrieval, listing, updating, and soft deletion of master data entities.
    
    Manifest IDs: MDM-001, MDM-002, MDM-003, MDM-008
    """
    # Clean up old data to ensure idempotency
    from sqlalchemy import delete
    from app.models.master_data import MasterDataEntity
    await db_session.execute(delete(MasterDataEntity).where(MasterDataEntity.tenant_id == tenant_id))
    await db_session.commit()

    service = MasterDataService(db_session)

    # 1. Create entities
    entity1 = await service.create_entity(
        tenant_id,
        MasterDataEntityCreate(
            category="leave_type",
            code="CL",
            name="Casual Leave",
            sort_order=2,
            extra_attributes={"max_days": 15},
        )
    )
    assert entity1.category == "leave_type"
    assert entity1.code == "CL"
    assert entity1.name == "Casual Leave"
    assert entity1.sort_order == 2
    assert entity1.extra_attributes == {"max_days": 15}

    # Entity 2 (lower sort order, should come first in listing)
    entity2 = await service.create_entity(
        tenant_id,
        MasterDataEntityCreate(
            category="leave_type",
            code="SL",
            name="Sick Leave",
            sort_order=1,
        )
    )

    # 2. Prevent Duplicate Code in the Same Category
    with pytest.raises(DuplicateRecordError):
        await service.create_entity(
            tenant_id,
            MasterDataEntityCreate(
                category="leave_type",
                code="CL",
                name="Duplicate Casual Leave",
            )
        )

    # 3. Retrieve Single Entity
    retrieved = await service.get_entity(tenant_id, entity1.id)
    assert retrieved.code == "CL"

    # 4. Get List (Sorted by sort_order, code)
    entities = await service.get_entities(tenant_id, "leave_type")
    assert len(entities) == 2
    assert entities[0].id == entity2.id  # sort_order 1
    assert entities[1].id == entity1.id  # sort_order 2

    # 5. Update Entity
    updated = await service.update_entity(
        tenant_id,
        entity1.id,
        MasterDataEntityUpdate(
            name="Casual Leave Updated",
            sort_order=0,
            extra_attributes={"max_days": 20},
        )
    )
    assert updated.name == "Casual Leave Updated"
    assert updated.sort_order == 0
    assert updated.extra_attributes == {"max_days": 20}

    # Verify listing order changed after update of sort_order
    entities_after_update = await service.get_entities(tenant_id, "leave_type")
    assert entities_after_update[0].id == entity1.id  # sort_order 0
    assert entities_after_update[1].id == entity2.id  # sort_order 1

    # 6. Delete (Soft delete)
    await service.delete_entity(tenant_id, entity1.id)

    # Retrieval should fail with ResourceNotFoundError
    with pytest.raises(ResourceNotFoundError):
        await service.get_entity(tenant_id, entity1.id)

    # Listing should now only contain the remaining active entity
    remaining_entities = await service.get_entities(tenant_id, "leave_type")
    assert len(remaining_entities) == 1
    assert remaining_entities[0].id == entity2.id
