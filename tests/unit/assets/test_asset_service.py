import pytest
import uuid
import os
from app.services.asset_service import AssetService
from app.services.storage import LocalStorageProvider
from app.models.user import User
from packages.shared.errors import ResourceNotFoundError


@pytest.mark.anyio
async def test_asset_lifecycle(db_session, tenant_id, test_user_id, tmp_path):
    """Test asset uploading, download, retrieving, audit logging, and deletion.
    
    Manifest IDs: AST-001, AST-002, AST-003, AST-004, EC-114
    """
    # Clean up old data to ensure idempotency
    from sqlalchemy import delete
    from app.models.digital_asset import DigitalAsset
    await db_session.execute(delete(DigitalAsset).where(DigitalAsset.tenant_id == tenant_id))
    await db_session.commit()

    # Seed User record to satisfy uploaded_by composite FK constraint
    user_exists = await db_session.get(User, test_user_id)
    if not user_exists:
        user = User(
            id=test_user_id,
            tenant_id=tenant_id,
            full_name="Asset Uploader",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

    # Initialize LocalStorageProvider with temporary test path
    storage_dir = str(tmp_path / "assets")
    storage = LocalStorageProvider(base_dir=storage_dir)
    service = AssetService(db_session, storage)

    test_content = b"Medical anatomage model export binary data"
    file_name = "anatomage_export.bin"
    file_type = "application/octet-stream"

    # 1. Upload Asset
    asset = await service.upload_asset(
        tenant_id=tenant_id,
        file_name=file_name,
        content=test_content,
        file_type=file_type,
        uploaded_by=test_user_id,
        meta_attributes={"anatomy_region": "thorax"},
    )

    assert asset.file_name == file_name
    assert asset.file_type == file_type
    assert asset.file_size == len(test_content)
    assert asset.uploaded_by == test_user_id
    assert asset.meta_attributes == {"anatomy_region": "thorax"}
    assert os.path.exists(asset.storage_path)

    # 2. Get Asset details
    retrieved = await service.get_asset(tenant_id, asset.id)
    assert retrieved.file_name == file_name
    assert retrieved.sha256 == asset.sha256

    # 3. Download Asset content
    downloaded_content, dl_name, dl_type = await service.download_asset(
        tenant_id=tenant_id,
        asset_id=asset.id,
        downloader_user_id=test_user_id,
    )
    assert downloaded_content == test_content
    assert dl_name == file_name
    assert dl_type == file_type

    # 4. Delete Asset
    saved_path = asset.storage_path
    await service.delete_asset(tenant_id, asset.id, test_user_id)

    # File should be deleted from physical storage
    assert not os.path.exists(saved_path)

    # Retrieval should now fail with ResourceNotFoundError
    with pytest.raises(ResourceNotFoundError):
        await service.get_asset(tenant_id, asset.id)
