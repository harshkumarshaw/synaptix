from __future__ import annotations

import datetime
import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from app.models import (
    AetcomRecord,
    ElectiveAllocation,
    FoundationCourseRecord,
    LogbookAssessment,
    LogbookEntry,
    WorkflowDefinition,
    WorkflowInstance,
)
from app.schemas import (
    AetcomReflectionSubmit,
    AetcomSignoffPayload,
    FoundationCourseHoursLog,
    FoundationCourseSignoffPayload,
    LogbookEntryCreate,
    LogbookEntryResponse,
    LogbookEntrySubmitRequest,
    LogbookSignoffRequest,
)
from app.services.audit_logger import write_audit_log
from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.db.session import get_db
from packages.shared.errors import (
    DuplicateRecordError,
    SynaptixError,
)
from packages.shared.logging import get_logger

logger = get_logger(__name__)


class LogbookServiceError(SynaptixError):
    """Exception raised for errors in the LogbookService."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        self.code = f"SNX-LOG-{code}"
        super().__init__(message, details)


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
        self,
        tenant_id: uuid.UUID,
        log_in: FoundationCourseHoursLog,
        actor_id: uuid.UUID | None = None,
    ) -> FoundationCourseRecord:
        # Check if record already exists
        stmt = select(FoundationCourseRecord).where(
            FoundationCourseRecord.tenant_id == tenant_id,
            FoundationCourseRecord.student_id == log_in.student_id,
            FoundationCourseRecord.module_name == log_in.module_name,
            FoundationCourseRecord.deleted_at.is_(None),
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
                updated_by=actor_id,
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
                "is_completed": record.is_completed,
            },
        )

        return record

    async def signoff_foundation_module(
        self,
        tenant_id: uuid.UUID,
        payload: FoundationCourseSignoffPayload,
        signed_off_by: uuid.UUID,
    ) -> FoundationCourseRecord:
        stmt = select(FoundationCourseRecord).where(
            FoundationCourseRecord.tenant_id == tenant_id,
            FoundationCourseRecord.student_id == payload.student_id,
            FoundationCourseRecord.module_name == payload.module_name,
            FoundationCourseRecord.deleted_at.is_(None),
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
                signoff_received_at=datetime.datetime.now(datetime.UTC),
                signed_off_by=signed_off_by,
                created_by=signed_off_by,
                updated_by=signed_off_by,
            )
            self.db.add(record)
        else:
            record.is_completed = True
            record.signoff_received_at = datetime.datetime.now(datetime.UTC)
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
                "signed_off_by": str(signed_off_by),
            },
        )

        return record

    async def get_student_foundation_progress(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID
    ) -> list[FoundationCourseRecord]:
        stmt = select(FoundationCourseRecord).where(
            FoundationCourseRecord.tenant_id == tenant_id,
            FoundationCourseRecord.student_id == student_id,
            FoundationCourseRecord.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # ============================================================================
    # AETCOM Tracking
    # ============================================================================

    async def submit_reflection(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        submit_in: AetcomReflectionSubmit,
        actor_id: uuid.UUID | None = None,
    ) -> AetcomRecord:
        # Check if record already exists
        stmt = select(AetcomRecord).where(
            AetcomRecord.tenant_id == tenant_id,
            AetcomRecord.student_id == student_id,
            AetcomRecord.module_code == submit_in.module_code,
            AetcomRecord.competency_code == submit_in.competency_code,
            AetcomRecord.professional_phase == submit_in.professional_phase,
            AetcomRecord.deleted_at.is_(None),
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
                updated_by=actor_id,
            )
            self.db.add(record)

        try:
            await self.db.flush()
        except IntegrityError as e:
            raise DuplicateRecordError(
                "Unique constraint violation submitting AETCOM reflection"
            ) from e

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
                "status": record.status,
            },
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
            AetcomRecord.deleted_at.is_(None),
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
                signed_off_at=datetime.datetime.now(datetime.UTC),
                created_by=signed_off_by,
                updated_by=signed_off_by,
            )
            self.db.add(record)
        else:
            record.status = "completed"
            record.signed_off_by = signed_off_by
            record.signed_off_at = datetime.datetime.now(datetime.UTC)
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
                "signed_off_by": str(signed_off_by),
            },
        )

        return record

    async def get_student_aetcom_records(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID, phase: str | None = None
    ) -> list[AetcomRecord]:
        stmt = select(AetcomRecord).where(
            AetcomRecord.tenant_id == tenant_id,
            AetcomRecord.student_id == student_id,
            AetcomRecord.deleted_at.is_(None),
        )
        if phase:
            stmt = stmt.where(AetcomRecord.professional_phase == phase)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # ============================================================================
    # Logbook Phase 2 Extensions
    # ============================================================================

    async def create_entry(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID, data: LogbookEntryCreate
    ) -> LogbookEntryResponse:
        """Student creates a new logbook entry."""
        # Future-dated check (LOG-E004)
        if data.activity_date > date.today():
            raise LogbookServiceError("001", "Future-dated logbook entry is not allowed")

        # Elective ownership check (LOG-002)
        if data.elective_id:
            alloc_stmt = select(ElectiveAllocation).where(
                ElectiveAllocation.tenant_id == tenant_id,
                ElectiveAllocation.student_id == data.student_id,
                ElectiveAllocation.elective_id == data.elective_id,
                ElectiveAllocation.deleted_at.is_(None),
            )
            alloc_res = await self.db.execute(alloc_stmt)
            allocation = alloc_res.scalar_one_or_none()
            if not allocation:
                raise LogbookServiceError("002", "Student is not allocated to this elective")

        # Create entry instance
        entry = LogbookEntry(
            tenant_id=tenant_id,
            student_id=data.student_id,
            subject_code=data.subject_code,
            elective_id=data.elective_id,
            professional_phase=data.professional_phase,
            competency_code=data.competency_code,
            nmc_level=data.nmc_level,
            is_core=data.is_core,
            activity_date=data.activity_date,
            activity_name=data.activity_name,
            reflection=data.reflection,
            status="pending",
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(entry)
        await self.db.flush()

        # Backdating logic (LOG-E001, LOG-E002, LOG-E003)
        gap_days = (date.today() - data.activity_date).days
        if gap_days > 7:
            entry.backdated = True
            if gap_days > 30:
                # Route to HOD via workflow engine
                def_stmt = select(WorkflowDefinition).where(
                    WorkflowDefinition.tenant_id == tenant_id,
                    WorkflowDefinition.code == "logbook_backdating_hod_review",
                )
                def_res = await self.db.execute(def_stmt)
                wf_def = def_res.scalar_one_or_none()
                if not wf_def:
                    wf_def = WorkflowDefinition(
                        tenant_id=tenant_id,
                        code="logbook_backdating_hod_review",
                        name="Logbook Backdating HOD Review",
                        steps={},
                    )
                    self.db.add(wf_def)
                    await self.db.flush()

                workflow = WorkflowInstance(
                    tenant_id=tenant_id,
                    definition_id=wf_def.id,
                    entity_type="exemption_grant",
                    entity_id=entry.id,
                    current_step="submitted",
                    status="initiated",
                    history=[],
                    context={},
                )
                self.db.add(workflow)
        else:
            entry.backdated = False

        await self.db.flush()

        # Write audit log
        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=user_id,
            action="CREATE_LOGBOOK_ENTRY",
            resource_type="logbook_entry",
            resource_id=entry.id,
            new_values={
                "student_id": str(entry.student_id),
                "subject_code": entry.subject_code,
                "elective_id": str(entry.elective_id) if entry.elective_id else None,
                "backdated": entry.backdated,
            },
        )

        return LogbookEntryResponse.model_validate(entry)

    async def submit_entry(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        entry_id: uuid.UUID,
        data: LogbookEntrySubmitRequest,
    ) -> LogbookEntryResponse:
        """Student submits entry for faculty review."""
        stmt = select(LogbookEntry).where(
            LogbookEntry.tenant_id == tenant_id,
            LogbookEntry.id == entry_id,
            LogbookEntry.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        entry = res.scalar_one_or_none()

        if not entry:
            raise LogbookServiceError("006", "Logbook entry not found")

        if entry.student_id != student_id:
            raise LogbookServiceError("AUTH-001", "Entry does not belong to this student")

        if entry.status != "pending":
            raise LogbookServiceError("003", f"Cannot submit entry in '{entry.status}' status")

        # Backdated > 30 days check: requires HOD approval (status in workflow needs to be approved or backdating_approved_by set)
        gap_days = (date.today() - entry.activity_date).days
        if gap_days > 30 and entry.backdating_approved_by is None:
            raise LogbookServiceError(
                "004", "Backdated entry (>30 days) requires HOD approval before submission"
            )

        entry.student_initials = data.student_initials
        entry.status = "submitted"
        entry.updated_by = student_id
        entry.updated_at = datetime.datetime.now(datetime.UTC)

        await self.db.flush()

        # Write audit log
        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=student_id,
            action="SUBMIT_LOGBOOK_ENTRY",
            resource_type="logbook_entry",
            resource_id=entry.id,
            new_values={
                "student_initials": data.student_initials,
                "status": "submitted",
            },
        )

        return LogbookEntryResponse.model_validate(entry)

    async def signoff_entry(
        self,
        tenant_id: uuid.UUID,
        faculty_id: uuid.UUID,
        entry_id: uuid.UUID,
        data: LogbookSignoffRequest,
    ) -> LogbookEntryResponse:
        """Faculty signs off on a submitted logbook entry."""
        stmt = select(LogbookEntry).where(
            LogbookEntry.tenant_id == tenant_id,
            LogbookEntry.id == entry_id,
            LogbookEntry.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        entry = res.scalar_one_or_none()

        if not entry:
            raise LogbookServiceError("006", "Logbook entry not found")

        if entry.status != "submitted":
            # LOG-E003: Check if entry already signed off (approved or rejected)
            if entry.status in ("approved", "rejected"):
                raise LogbookServiceError("005", "Entry already signed off")
            raise LogbookServiceError("005", f"Cannot sign off entry in '{entry.status}' status")

        # Apply signoff
        entry.rating = data.rating
        entry.faculty_decision = data.faculty_decision
        entry.faculty_initials = data.faculty_initials
        entry.signed_off_by = faculty_id
        entry.signed_off_at = datetime.datetime.now(datetime.UTC)
        entry.status = "approved" if data.faculty_decision == "C" else "rejected"
        entry.updated_by = faculty_id
        entry.updated_at = datetime.datetime.now(datetime.UTC)

        await self.db.flush()

        # Recalculate IA marks for this subject/phase
        if entry.subject_code:
            await self._recalculate_ia_marks(
                tenant_id, entry.student_id, entry.subject_code, entry.professional_phase
            )

        # Write audit log
        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=faculty_id,
            action="SIGNOFF_LOGBOOK_ENTRY",
            resource_type="logbook_entry",
            resource_id=entry.id,
            new_values={
                "rating": data.rating,
                "faculty_decision": data.faculty_decision,
                "new_status": entry.status,
            },
        )

        return LogbookEntryResponse.model_validate(entry)

    async def _recalculate_ia_marks(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        subject_code: str,
        professional_phase: str,
    ) -> None:
        """Recalculate logbook_assessments row for the given student/subject/phase."""
        # Count approved entries
        total_stmt = select(func.count(LogbookEntry.id)).where(
            LogbookEntry.tenant_id == tenant_id,
            LogbookEntry.student_id == student_id,
            LogbookEntry.subject_code == subject_code,
            LogbookEntry.professional_phase == professional_phase,
            LogbookEntry.status == "approved",
            LogbookEntry.deleted_at.is_(None),
        )
        total_res = await self.db.execute(total_stmt)
        total_entries = total_res.scalar() or 0

        # Count certified entries (faculty_decision = 'C')
        completed_stmt = select(func.count(LogbookEntry.id)).where(
            LogbookEntry.tenant_id == tenant_id,
            LogbookEntry.student_id == student_id,
            LogbookEntry.subject_code == subject_code,
            LogbookEntry.professional_phase == professional_phase,
            LogbookEntry.status == "approved",
            LogbookEntry.faculty_decision == "C",
            LogbookEntry.deleted_at.is_(None),
        )
        completed_res = await self.db.execute(completed_stmt)
        completed_entries = completed_res.scalar() or 0

        # Get IA Config with fallbacks
        ia_weight_pct, subject_ia_max = await self._get_ia_config(
            tenant_id, subject_code, professional_phase
        )

        # Calculate
        completion_pct = (completed_entries / total_entries * 100) if total_entries > 0 else 0.0
        raw_marks = (
            Decimal(str(completion_pct / 100)) * (ia_weight_pct / Decimal("100")) * subject_ia_max
        )

        # Enforce 20% cap (LOG-NMC-012)
        cap = Decimal("0.20") * subject_ia_max
        ia_marks_awarded = min(raw_marks, cap)

        # If weight is configured above 20% (institutional misconfiguration), log compliance incident
        if ia_weight_pct > Decimal("20.00"):
            await write_audit_log(
                db=self.db,
                tenant_id=tenant_id,
                actor_user_id=None,
                action="COMPLIANCE_INCIDENT",
                resource_type="logbook_assessment",
                resource_id=student_id,
                new_values={
                    "incident_type": "ia_weight_exceeds_20_pct",
                    "subject_code": subject_code,
                    "configured_weight_pct": float(ia_weight_pct),
                    "cap_applied": True,
                },
            )

        # Upsert logbook_assessments row
        assess_stmt = select(LogbookAssessment).where(
            LogbookAssessment.tenant_id == tenant_id,
            LogbookAssessment.student_id == student_id,
            LogbookAssessment.subject_code == subject_code,
            LogbookAssessment.professional_phase == professional_phase,
        )
        assess_res = await self.db.execute(assess_stmt)
        existing = assess_res.scalar_one_or_none()

        if existing:
            existing.total_entries = total_entries
            existing.completed_entries = completed_entries
            existing.ia_marks_pct = ia_weight_pct
            existing.ia_marks_awarded = ia_marks_awarded
            existing.is_complete = total_entries > 0 and completed_entries == total_entries
            existing.updated_at = datetime.datetime.now(datetime.UTC)
        else:
            new_assessment = LogbookAssessment(
                tenant_id=tenant_id,
                student_id=student_id,
                subject_code=subject_code,
                professional_phase=professional_phase,
                total_entries=total_entries,
                completed_entries=completed_entries,
                ia_marks_pct=ia_weight_pct,
                ia_marks_awarded=ia_marks_awarded,
                is_complete=(total_entries > 0 and completed_entries == total_entries),
            )
            self.db.add(new_assessment)

        await self.db.flush()

    async def _get_ia_config(
        self, tenant_id: uuid.UUID, subject_code: str, professional_phase: str
    ) -> tuple[Decimal, Decimal]:
        """Get IA config (weight% and max marks) with fallback defaults (D8 debt warning)."""
        # Falls back to default values
        import logging

        logging.warning(
            "MDM config not found for IA: %s/%s. Using defaults (10%%, 40 marks).",
            subject_code,
            professional_phase,
        )
        return Decimal("10.00"), Decimal("40.00")

    async def get_student_entries(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        subject_code: str | None = None,
        professional_phase: str | None = None,
        status: str | None = None,
        competency_code: str | None = None,
        is_core: bool | None = None,
    ) -> list[LogbookEntry]:
        """List logbook entries for a student with optional filters."""
        stmt = select(LogbookEntry).where(
            LogbookEntry.tenant_id == tenant_id,
            LogbookEntry.student_id == student_id,
            LogbookEntry.deleted_at.is_(None),
        )

        if subject_code is not None:
            stmt = stmt.where(LogbookEntry.subject_code == subject_code)
        if professional_phase is not None:
            stmt = stmt.where(LogbookEntry.professional_phase == professional_phase)
        if status is not None:
            stmt = stmt.where(LogbookEntry.status == status)
        if competency_code is not None:
            stmt = stmt.where(LogbookEntry.competency_code == competency_code)
        if is_core is not None:
            stmt = stmt.where(LogbookEntry.is_core == is_core)

        # Order by activity_date descending
        stmt = stmt.order_by(LogbookEntry.activity_date.desc())

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_ia_assessment(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        subject_code: str,
        professional_phase: str,
    ) -> LogbookAssessment:
        """Get IA marks assessment for a student's subject/phase. Returns zeroed fallback if none."""
        stmt = select(LogbookAssessment).where(
            LogbookAssessment.tenant_id == tenant_id,
            LogbookAssessment.student_id == student_id,
            LogbookAssessment.subject_code == subject_code,
            LogbookAssessment.professional_phase == professional_phase,
            LogbookAssessment.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        assessment = res.scalar_one_or_none()

        if not assessment:
            # Return a zero-value fallback without persisting it
            return LogbookAssessment(
                tenant_id=tenant_id,
                student_id=student_id,
                subject_code=subject_code,
                professional_phase=professional_phase,
                total_entries=0,
                completed_entries=0,
                ia_marks_pct=Decimal("0.00"),
                ia_marks_awarded=Decimal("0.00"),
                is_complete=False,
            )

        return assessment
