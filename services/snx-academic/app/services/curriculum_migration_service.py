from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum_migration import CurriculumMigrationAudit
from app.schemas.curriculum_migration import CurriculumMigrationAuditCreate
from app.services.audit_logger import write_audit_log
from packages.shared.db.session import get_db
from packages.shared.logging import get_logger

logger = get_logger(__name__)


class CurriculumMigrationService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def record_migration(
        self,
        tenant_id: uuid.UUID,
        migration_in: CurriculumMigrationAuditCreate,
        actor_id: uuid.UUID | None = None,
    ) -> CurriculumMigrationAudit:
        if not actor_id:
            raise ValueError("actor_id is required to record a curriculum migration.")

        audit = CurriculumMigrationAudit(
            tenant_id=tenant_id,
            student_id=migration_in.student_id,
            from_curriculum_id=migration_in.from_curriculum_id,
            to_curriculum_id=migration_in.to_curriculum_id,
            approved_by=actor_id,
            migration_details=migration_in.migration_details,
            migrated_at=datetime.now(UTC),
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(audit)
        await self.db.flush()

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="MIGRATE_CURRICULUM",
            resource_type="curriculum_migration",
            resource_id=audit.id,
            new_values={
                "student_id": str(audit.student_id),
                "from_curriculum_id": str(audit.from_curriculum_id),
                "to_curriculum_id": str(audit.to_curriculum_id),
                "approved_by": str(audit.approved_by),
            },
        )

        return audit

    async def get_migration_history(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID
    ) -> list[CurriculumMigrationAudit]:
        stmt = (
            select(CurriculumMigrationAudit)
            .where(
                CurriculumMigrationAudit.tenant_id == tenant_id,
                CurriculumMigrationAudit.student_id == student_id,
            )
            .order_by(CurriculumMigrationAudit.migrated_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
