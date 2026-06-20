from __future__ import annotations

import uuid
import hashlib
from typing import Annotated, Any
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from packages.shared.db.session import get_db
from packages.shared.errors import ResourceNotFoundError
from packages.shared.logging import get_logger
from app.models.digital_asset import DigitalAsset
from app.services.storage import StorageProvider, LocalStorageProvider
from app.services.audit_logger import write_audit_log

logger = get_logger(__name__)


class AssetService:
    def __init__(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],
        storage: Annotated[StorageProvider, Depends(LocalStorageProvider)],
    ) -> None:
        self.db = db
        self.storage = storage

    async def upload_asset(
        self,
        tenant_id: uuid.UUID,
        file_name: str,
        content: bytes,
        file_type: str,
        uploaded_by: uuid.UUID,
        meta_attributes: dict[str, Any] | None = None,
    ) -> DigitalAsset:
        # Compute SHA256 checksum
        sha256 = hashlib.sha256(content).hexdigest()
        file_size = len(content)

        # Save to storage provider
        storage_path = await self.storage.save(file_name, content, tenant_id)

        # Create record in DB
        asset = DigitalAsset(
            tenant_id=tenant_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            storage_path=storage_path,
            uploaded_by=uploaded_by,
            sha256=sha256,
            meta_attributes=meta_attributes or {},
        )
        self.db.add(asset)
        await self.db.flush()
        
        # Log to global audit log
        await write_audit_log(
            self.db,
            tenant_id=tenant_id,
            actor_user_id=uploaded_by,
            action="ASSET_UPLOAD",
            resource_type="digital_asset",
            resource_id=asset.id,
            new_values={
                "file_name": file_name,
                "file_size": file_size,
                "sha256": sha256,
            },
        )
        
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def get_asset(self, tenant_id: uuid.UUID, asset_id: uuid.UUID) -> DigitalAsset:
        stmt = (
            select(DigitalAsset)
            .options(joinedload(DigitalAsset.uploader))
            .where(
                DigitalAsset.tenant_id == tenant_id,
                DigitalAsset.id == asset_id,
                DigitalAsset.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        asset = res.scalar_one_or_none()
        if not asset:
            raise ResourceNotFoundError(f"DigitalAsset {asset_id} not found")
        return asset

    async def download_asset(
        self, tenant_id: uuid.UUID, asset_id: uuid.UUID, downloader_user_id: uuid.UUID
    ) -> tuple[bytes, str, str]:
        asset = await self.get_asset(tenant_id, asset_id)
        
        # Read from storage provider
        content = await self.storage.read(asset.storage_path)

        # Log to global audit log (DPDP Act download tracking)
        await write_audit_log(
            self.db,
            tenant_id=tenant_id,
            actor_user_id=downloader_user_id,
            action="ASSET_DOWNLOAD",
            resource_type="digital_asset",
            resource_id=asset.id,
            new_values={"file_name": asset.file_name},
        )
        await self.db.commit()

        return content, asset.file_name, asset.file_type

    async def delete_asset(self, tenant_id: uuid.UUID, asset_id: uuid.UUID, actor_user_id: uuid.UUID) -> None:
        asset = await self.get_asset(tenant_id, asset_id)
        
        # Soft delete
        from datetime import datetime, timezone
        asset.deleted_at = datetime.now(timezone.utc)
        
        # Delete physical file from storage provider
        try:
            await self.storage.delete(asset.storage_path)
        except Exception as e:
            logger.error("Failed to delete asset from physical storage", extra={"path": asset.storage_path, "error": str(e)})

        # Log to audit log
        await write_audit_log(
            self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="ASSET_DELETE",
            resource_type="digital_asset",
            resource_id=asset.id,
        )
        
        await self.db.commit()
