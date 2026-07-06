from __future__ import annotations

import datetime
import uuid
from typing import Any

from pydantic import BaseModel


class CurriculumMigrationAuditCreate(BaseModel):
    student_id: uuid.UUID
    from_curriculum_id: uuid.UUID
    to_curriculum_id: uuid.UUID
    migration_details: dict[str, Any] | None = None


class CurriculumMigrationAuditResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    from_curriculum_id: uuid.UUID
    to_curriculum_id: uuid.UUID
    migrated_at: datetime.datetime
    approved_by: uuid.UUID
    migration_details: dict[str, Any] | None

    class Config:
        from_attributes = True
