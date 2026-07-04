import pytest
import uuid
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from packages.shared.mdm.config_service import MdmConfigService
from app.services.master_data_service import MasterDataService


@pytest.mark.anyio
async def test_mdm_004_reference_constraint_on_delete(test_db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """MDM-004: Deleting a referenced tenant is blocked by mdm_configs RESTRICT constraint."""
    # Seed an mdm_configs record first
    await test_db_session.execute(
        text("""
            INSERT INTO mdm_configs (tenant_id, config_key, config_value, description)
            VALUES (:tenant_id, 'test.restrict.key', '{"test": 1}'::jsonb, 'Test RESTRICT')
        """),
        {"tenant_id": tenant_id}
    )
    await test_db_session.commit()

    # Attempt to delete the tenant — should raise IntegrityError due to RESTRICT on mdm_configs.tenant_id
    with pytest.raises(IntegrityError):
        await test_db_session.execute(
            text("DELETE FROM tenants WHERE id = :id"), {"id": tenant_id}
        )
        await test_db_session.commit()
    
    await test_db_session.rollback()


@pytest.mark.anyio
async def test_mdm_005_medical_onboarding_templates(test_db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """MDM-005: Medical department onboarding templates exist in MDM seed."""
    med_template = {
        "institution_type": "medical",
        "regulatory_body": "NMC",
        "departments": ["Anatomy", "Physiology"],
        "documents_required": ["NMC_Registration"]
    }
    await test_db_session.execute(
        text("""
            INSERT INTO mdm_configs (tenant_id, config_key, config_value, description)
            VALUES (:tenant_id, 'onboarding.template.medical', CAST(:med_value AS jsonb), 'Med onboarding')
            ON CONFLICT (tenant_id, config_key) DO NOTHING
        """),
        {
            "tenant_id": tenant_id,
            "med_value": '{"institution_type": "medical", "regulatory_body": "NMC", "departments": ["Anatomy", "Physiology"], "documents_required": ["NMC_Registration"]}'
        }
    )
    await test_db_session.commit()

    mdm = MdmConfigService(test_db_session)
    template = await mdm.get(tenant_id, "onboarding.template.medical")
    assert template is not None
    assert template["regulatory_body"] == "NMC"
    assert "Anatomy" in template["departments"]


@pytest.mark.anyio
async def test_mdm_006_nursing_onboarding_templates(test_db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """MDM-006: Nursing department onboarding templates exist in MDM seed."""
    await test_db_session.execute(
        text("""
            INSERT INTO mdm_configs (tenant_id, config_key, config_value, description)
            VALUES (:tenant_id, 'onboarding.template.nursing', CAST(:nursing_value AS jsonb), 'Nursing onboarding')
            ON CONFLICT (tenant_id, config_key) DO NOTHING
        """),
        {
            "tenant_id": tenant_id,
            "nursing_value": '{"institution_type": "nursing", "regulatory_body": "INC", "departments": ["Fundamentals of Nursing"], "documents_required": ["INC_Registration"]}'
        }
    )
    await test_db_session.commit()

    mdm = MdmConfigService(test_db_session)
    template = await mdm.get(tenant_id, "onboarding.template.nursing")
    assert template is not None
    assert template["regulatory_body"] == "INC"
    assert "Fundamentals of Nursing" in template["departments"]


@pytest.mark.anyio
async def test_mdm_007_csv_import_validation(test_db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """MDM-007: CSV import rejects malformed rows and reports line numbers."""
    from app.models.master_data import MasterDataEntity
    from sqlalchemy import delete

    # Clean up master data for this category to ensure clear counts
    await test_db_session.execute(
        delete(MasterDataEntity).where(
            MasterDataEntity.tenant_id == tenant_id,
            MasterDataEntity.category == "csv_import_test"
        )
    )
    await test_db_session.commit()

    service = MasterDataService(test_db_session)
    
    csv_data = """category,code,name,sort_order
csv_import_test,C1,Name One,1
csv_import_test,C2,Name Two,2
csv_import_test,,Missing Code,3
csv_import_test,C4,Name Four,4
csv_import_test,C4,Duplicate Code,5
"""
    result = await service.import_csv(tenant_id, csv_data)
    
    # Expected result:
    # Row 1 (header ignored)
    # Row 2 (csv_import_test,C1) -> success
    # Row 3 (csv_import_test,C2) -> success
    # Row 4 (csv_import_test,,Missing Code) -> fail (line 4: missing code)
    # Row 5 (csv_import_test,C4) -> success
    # Row 6 (csv_import_test,C4) -> fail (line 6: duplicate code)
    
    assert result["imported"] == 3
    assert len(result["errors"]) == 2
    
    # Line 4 should have error
    line_4_errs = [e for e in result["errors"] if e["line"] == 4]
    assert len(line_4_errs) == 1
    assert "required" in line_4_errs[0]["error"]
    
    # Line 6 should have error
    line_6_errs = [e for e in result["errors"] if e["line"] == 6]
    assert len(line_6_errs) == 1
    assert "already exists" in line_6_errs[0]["error"]
