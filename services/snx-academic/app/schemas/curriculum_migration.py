from __future__ import annotations

import uuid
import datetime
from typing import Optional, Any
from pydantic import BaseModel

class CurriculumMigrationAuditCreate(BaseModel):
    student_id: uuid.UUID
    from_curriculum_id: uuid.UUID
    to_curriculum_id: uuid.UUID
    migration_details: Optional[dict[str, Any]] = None

class CurriculumMigrationAuditResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    from_curriculum_id: uuid.UUID
    to_curriculum_id: uuid.UUID
    migrated_at: datetime.datetime
    approved_by: uuid.UUID
    migration_details: Optional[dict[str, Any]]

    class Config:
        from_attributes = True
