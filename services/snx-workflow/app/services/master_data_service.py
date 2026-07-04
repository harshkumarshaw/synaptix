from __future__ import annotations

import uuid
from datetime import UTC
from typing import Annotated

from app.models.master_data import MasterDataEntity
from app.schemas.master_data import MasterDataEntityCreate, MasterDataEntityUpdate
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.db.session import get_db
from packages.shared.errors import DuplicateRecordError, ResourceNotFoundError
from packages.shared.logging import get_logger

logger = get_logger(__name__)


class MasterDataService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def get_entities(
        self,
        tenant_id: uuid.UUID,
        category: str,
        curriculum_id: uuid.UUID | None = None,
    ) -> list[MasterDataEntity]:
        stmt = select(MasterDataEntity).where(
            MasterDataEntity.tenant_id == tenant_id,
            MasterDataEntity.category == category,
            MasterDataEntity.deleted_at.is_(None),
        )
        if curriculum_id is not None:
            stmt = stmt.where(MasterDataEntity.curriculum_id == curriculum_id)
        else:
            stmt = stmt.where(MasterDataEntity.curriculum_id.is_(None))

        stmt = stmt.order_by(MasterDataEntity.sort_order, MasterDataEntity.code)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_entity(self, tenant_id: uuid.UUID, entity_id: uuid.UUID) -> MasterDataEntity:
        stmt = select(MasterDataEntity).where(
            MasterDataEntity.tenant_id == tenant_id,
            MasterDataEntity.id == entity_id,
            MasterDataEntity.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        entity = res.scalar_one_or_none()
        if not entity:
            raise ResourceNotFoundError(f"MasterDataEntity {entity_id} not found")
        return entity

    async def create_entity(
        self, tenant_id: uuid.UUID, schema: MasterDataEntityCreate
    ) -> MasterDataEntity:
        # Check if active code exists under category
        stmt = select(MasterDataEntity).where(
            MasterDataEntity.tenant_id == tenant_id,
            MasterDataEntity.category == schema.category,
            MasterDataEntity.code == schema.code,
            MasterDataEntity.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise DuplicateRecordError(
                f"Master data entity with code '{schema.code}' already exists under category '{schema.category}'"
            )

        entity = MasterDataEntity(
            tenant_id=tenant_id,
            curriculum_id=schema.curriculum_id,
            category=schema.category,
            code=schema.code,
            name=schema.name,
            extra_attributes=schema.extra_attributes,
            sort_order=schema.sort_order,
            is_active=schema.is_active,
        )
        self.db.add(entity)
        try:
            await self.db.commit()
            await self.db.refresh(entity)
        except IntegrityError as e:
            await self.db.rollback()
            raise DuplicateRecordError("Integrity constraint violation on creation") from e

        return entity

    async def update_entity(
        self, tenant_id: uuid.UUID, entity_id: uuid.UUID, schema: MasterDataEntityUpdate
    ) -> MasterDataEntity:
        entity = await self.get_entity(tenant_id, entity_id)

        if schema.name is not None:
            entity.name = schema.name
        if schema.curriculum_id is not None:
            entity.curriculum_id = schema.curriculum_id
        if schema.extra_attributes is not None:
            entity.extra_attributes = schema.extra_attributes
        if schema.sort_order is not None:
            entity.sort_order = schema.sort_order
        if schema.is_active is not None:
            entity.is_active = schema.is_active

        try:
            await self.db.commit()
            await self.db.refresh(entity)
        except IntegrityError as e:
            await self.db.rollback()
            raise DuplicateRecordError("Integrity constraint violation on update") from e

        return entity

    async def delete_entity(self, tenant_id: uuid.UUID, entity_id: uuid.UUID) -> None:
        entity = await self.get_entity(tenant_id, entity_id)

        # Soft delete
        from datetime import datetime

        entity.deleted_at = datetime.now(UTC)
        await self.db.commit()

    async def import_csv(self, tenant_id: uuid.UUID, csv_content: str) -> dict[str, Any]:
        """Bulk import entities from CSV content. Returns {imported: X, errors: [{line: Y, error: Z}]}.
        
        CSV format: category,code,name,sort_order
        """
        import csv
        from io import StringIO

        reader = csv.reader(StringIO(csv_content.strip()))
        imported_count = 0
        errors = []
        
        # Skip header if present
        header = next(reader, None)
        has_header = True
        if header and len(header) >= 3 and header[0].lower() not in ["category", "category_code"]:
            # No header, it is a data row, reset reader or parse it
            has_header = False
            reader = csv.reader(StringIO(csv_content.strip()))

        line_num = 1 if has_header else 0
        for row in reader:
            line_num += 1
            if not row:
                continue
            if len(row) < 3:
                errors.append({"line": line_num, "error": "Insufficient columns, need category, code, name"})
                continue
            
            category, code, name = row[0].strip(), row[1].strip(), row[2].strip()
            sort_order = 0
            if len(row) >= 4:
                try:
                    sort_order = int(row[3].strip())
                except ValueError:
                    pass
            
            if not category or not code or not name:
                errors.append({"line": line_num, "error": "category, code, and name are required"})
                continue
            
            try:
                # Use create_entity to validate duplicates and save
                await self.create_entity(
                    tenant_id,
                    MasterDataEntityCreate(
                        category=category,
                        code=code,
                        name=name,
                        sort_order=sort_order,
                    )
                )
                imported_count += 1
            except Exception as e:
                errors.append({"line": line_num, "error": str(e)})
                
        return {"imported": imported_count, "errors": errors}
