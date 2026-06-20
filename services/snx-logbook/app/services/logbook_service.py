from __future__ import annotations

import uuid
import datetime
from datetime import timezone
from typing import Annotated, List, Optional
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from packages.shared.db.session import get_db
from packages.shared.errors import (
    ResourceNotFoundError,
    ValidationError,
    DuplicateRecordError,
)
from packages.shared.logging import get_logger
from app.models.logbook import FoundationCourseRecord, AetcomRecord
from app.schemas.logbook import (
    FoundationCourseHoursLog,
    FoundationCourseSignoffPayload,
    AetcomReflectionSubmit,
    AetcomSignoffPayload,
)
from app.services.audit_logger import write_audit_log

logger = get_logger(__name__)


# Default required hours per foundation course module based on standard curriculum
DEFAULT_REQUIRED_HOURS = {
    "orientation": 30.0,
    "skills_acquisition": 35.0,
    "professional_development": 40.0,
    "language_computer": 40.0,
    "sports_yoga": 20.0,
    "hospital_visits": 10.0,
}


class LogbookService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    # ============================================================================
    # Foundation Course Progress
    # ============================================================================

    async def log_foundation_hours(
        self, tenant_id: uuid.UUID, log_in: FoundationCourseHoursLog, actor_id: Optional[uuid.UUID] = None
    ) -> FoundationCourseRecord:
        # Check if record already exists
        stmt = select(FoundationCourseRecord).where(
            FoundationCourseRecord.tenant_id == tenant_id,
            FoundationCourseRecord.student_id == log_in.student_id,
            FoundationCourseRecord.module_name == log_in.module_name,
            FoundationCourseRecord.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()

        required = DEFAULT_REQUIRED_HOURS.get(log_in.module_name, 20.0)

        if record:
            record.completed_hours = float(record.completed_hours) + log_in.hours
            if record.completed_hours >= required:
                record.is_completed = True
            record.updated_by = actor_id
        else:
            completed = log_in.hours
            is_comp = completed >= required
            record = FoundationCourseRecord(
                tenant_id=tenant_id,
                student_id=log_in.student_id,
                module_name=log_in.module_name,
                completed_hours=completed,
                required_hours=required,
                is_completed=is_comp,
                created_by=actor_id,
                updated_by=actor_id
            )
            self.db.add(record)

        await self.db.flush()

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="LOG_FOUNDATION_HOURS",
            resource_type="foundation_course_record",
            resource_id=record.id,
            new_values={
                "module_name": record.module_name,
                "completed_hours": float(record.completed_hours),
                "is_completed": record.is_completed
            }
        )

        return record

    async def signoff_foundation_module(
        self, tenant_id: uuid.UUID, payload: FoundationCourseSignoffPayload, signed_off_by: uuid.UUID
    ) -> FoundationCourseRecord:
        stmt = select(FoundationCourseRecord).where(
            FoundationCourseRecord.tenant_id == tenant_id,
            FoundationCourseRecord.student_id == payload.student_id,
            FoundationCourseRecord.module_name == payload.module_name,
            FoundationCourseRecord.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            required = DEFAULT_REQUIRED_HOURS.get(payload.module_name, 20.0)
            # Create a completed/signed-off record directly
            record = FoundationCourseRecord(
                tenant_id=tenant_id,
                student_id=payload.student_id,
                module_name=payload.module_name,
                completed_hours=required,
                required_hours=required,
                is_completed=True,
                signoff_received_at=datetime.datetime.now(timezone.utc),
                signed_off_by=signed_off_by,
                created_by=signed_off_by,
                updated_by=signed_off_by
            )
            self.db.add(record)
        else:
            record.is_completed = True
            record.signoff_received_at = datetime.datetime.now(timezone.utc)
            record.signed_off_by = signed_off_by
            record.updated_by = signed_off_by

        await self.db.flush()

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=signed_off_by,
            action="SIGNOFF_FOUNDATION_COURSE",
            resource_type="foundation_course_record",
            resource_id=record.id,
            new_values={
                "module_name": record.module_name,
                "is_completed": True,
                "signed_off_by": str(signed_off_by)
            }
        )

        return record

    async def get_student_foundation_progress(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID
    ) -> List[FoundationCourseRecord]:
        stmt = select(FoundationCourseRecord).where(
            FoundationCourseRecord.tenant_id == tenant_id,
            FoundationCourseRecord.student_id == student_id,
            FoundationCourseRecord.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # ============================================================================
    # AETCOM Tracking
    # ============================================================================

    async def submit_reflection(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID, submit_in: AetcomReflectionSubmit, actor_id: Optional[uuid.UUID] = None
    ) -> AetcomRecord:
        # Check if record already exists
        stmt = select(AetcomRecord).where(
            AetcomRecord.tenant_id == tenant_id,
            AetcomRecord.student_id == student_id,
            AetcomRecord.module_code == submit_in.module_code,
            AetcomRecord.competency_code == submit_in.competency_code,
            AetcomRecord.professional_phase == submit_in.professional_phase,
            AetcomRecord.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()

        if record:
            record.reflection_text = submit_in.reflection_text
            record.status = "reflection_submitted"
            record.updated_by = actor_id
        else:
            record = AetcomRecord(
                tenant_id=tenant_id,
                student_id=student_id,
                module_code=submit_in.module_code,
                competency_code=submit_in.competency_code,
                professional_phase=submit_in.professional_phase,
                status="reflection_submitted",
                reflection_text=submit_in.reflection_text,
                created_by=actor_id,
                updated_by=actor_id
            )
            self.db.add(record)

        try:
            await self.db.flush()
        except IntegrityError as e:
            raise DuplicateRecordError("Unique constraint violation submitting AETCOM reflection") from e

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="SUBMIT_AETCOM_REFLECTION",
            resource_type="aetcom_record",
            resource_id=record.id,
            new_values={
                "module_code": record.module_code,
                "competency_code": record.competency_code,
                "status": record.status
            }
        )

        return record

    async def signoff_aetcom_competency(
        self, tenant_id: uuid.UUID, payload: AetcomSignoffPayload, signed_off_by: uuid.UUID
    ) -> AetcomRecord:
        stmt = select(AetcomRecord).where(
            AetcomRecord.tenant_id == tenant_id,
            AetcomRecord.student_id == payload.student_id,
            AetcomRecord.module_code == payload.module_code,
            AetcomRecord.competency_code == payload.competency_code,
            AetcomRecord.professional_phase == payload.professional_phase,
            AetcomRecord.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            # Create a completed record directly
            record = AetcomRecord(
                tenant_id=tenant_id,
                student_id=payload.student_id,
                module_code=payload.module_code,
                competency_code=payload.competency_code,
                professional_phase=payload.professional_phase,
                status="completed",
                signed_off_by=signed_off_by,
                signed_off_at=datetime.datetime.now(timezone.utc),
                created_by=signed_off_by,
                updated_by=signed_off_by
            )
            self.db.add(record)
        else:
            record.status = "completed"
            record.signed_off_by = signed_off_by
            record.signed_off_at = datetime.datetime.now(timezone.utc)
            record.updated_by = signed_off_by

        await self.db.flush()

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=signed_off_by,
            action="SIGNOFF_AETCOM",
            resource_type="aetcom_record",
            resource_id=record.id,
            new_values={
                "module_code": record.module_code,
                "competency_code": record.competency_code,
                "status": "completed",
                "signed_off_by": str(signed_off_by)
            }
        )

        return record

    async def get_student_aetcom_records(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID, phase: Optional[str] = None
    ) -> List[AetcomRecord]:
        stmt = select(AetcomRecord).where(
            AetcomRecord.tenant_id == tenant_id,
            AetcomRecord.student_id == student_id,
            AetcomRecord.deleted_at.is_(None)
        )
        if phase:
            stmt = stmt.where(AetcomRecord.professional_phase == phase)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
