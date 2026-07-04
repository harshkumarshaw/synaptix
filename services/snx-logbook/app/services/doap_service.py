"""DOAP Skills service implementation."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from app.models.logbook_phase2 import DoapSessionRecord, LogbookEntry
from app.models.stubs import WorkflowDefinition, WorkflowInstance
from app.schemas.doap import (
    DoapSessionCreate,
    DoapSessionResponse,
    DoapStateResponse,
)
from app.services.audit_logger import write_audit_log
from app.services.doap_validators import (
    compute_certified_stages,
    derive_current_state,
    validate_rating_decision,
    validate_stage_progression,
)
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.db.session import get_db
from packages.shared.mdm.config_service import MdmConfigService


class DoapServiceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class DoapService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def submit_doap_session(
        self,
        tenant_id: UUID,
        user_id: UUID,
        data: DoapSessionCreate,
    ) -> DoapSessionResponse:
        """
        Create a DOAP session record after validating state machine rules.
        Auto-creates corresponding logbook_entry. Triggers remediation workflow on Re.
        """
        # Step 1: Fetch existing records for this student + competency
        existing = await self.db.execute(
            select(DoapSessionRecord).where(
                DoapSessionRecord.tenant_id == tenant_id,
                DoapSessionRecord.student_id == data.student_id,
                DoapSessionRecord.competency_code == data.competency_code,
                DoapSessionRecord.deleted_at.is_(None),
            )
        )
        existing_records = existing.scalars().all()
        certified_stages = compute_certified_stages(existing_records)

        # Step 2: Validate stage progression
        progression_result = validate_stage_progression(
            proposed_stage=data.stage,
            certified_stages=certified_stages,
            attempt_type=data.attempt_type,
        )
        if not progression_result.is_valid:
            raise DoapServiceError(
                progression_result.error_code,
                progression_result.error_message,
            )

        # Step 3: Validate rating-decision consistency
        rating_result = validate_rating_decision(data.rating, data.faculty_decision)
        if not rating_result.is_valid:
            raise DoapServiceError(
                rating_result.error_code,
                rating_result.error_message,
            )

        # Step 4: Insert DOAP record
        new_record = DoapSessionRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=data.student_id,
            session_id=data.session_id,
            competency_code=data.competency_code,
            nmc_level=data.nmc_level,
            is_core=data.is_core,
            stage=data.stage,
            rating=data.rating,
            attempt_type=data.attempt_type,
            faculty_decision=data.faculty_decision,
            faculty_id=data.faculty_id,
            evidence_asset_ids=[str(uid) for uid in data.evidence_asset_ids],
            notes=data.notes,
            signed_off_at=datetime.now(UTC),
        )
        self.db.add(new_record)
        await self.db.flush()  # Get ID before audit log / FK linkage

        # Step 5: Auto-create logbook entry (DOAP-008)
        logbook_entry = LogbookEntry(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=data.student_id,
            elective_id=None,
            subject_code=await self._infer_subject_code(tenant_id, data.competency_code),
            competency_code=data.competency_code,
            professional_phase="Phase I",  # Safe default since DOAP table lacks professional_phase
            nmc_level=data.nmc_level,
            is_core=data.is_core,
            activity_date=datetime.now(UTC).date(),
            activity_name=f"DOAP {data.stage} record for {data.competency_code}",
            rating=data.rating,
            attempt_type=data.attempt_type,
            faculty_decision=data.faculty_decision,
            status="approved" if data.faculty_decision == "C" else "pending",
            signed_off_by=data.faculty_id,
            signed_off_at=datetime.now(UTC),
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(logbook_entry)

        # Step 6: Trigger remediation workflow if Re decision (DOAP-006)
        if data.faculty_decision == "Re":
            def_stmt = select(WorkflowDefinition).where(
                WorkflowDefinition.tenant_id == tenant_id,
                WorkflowDefinition.code == "doap_remediation",
            )
            def_res = await self.db.execute(def_stmt)
            wf_def = def_res.scalar_one_or_none()
            if not wf_def:
                wf_def = WorkflowDefinition(
                    tenant_id=tenant_id,
                    code="doap_remediation",
                    name="DOAP Remediation Workflow",
                    steps={},
                )
                self.db.add(wf_def)
                await self.db.flush()

            workflow = WorkflowInstance(
                id=uuid4(),
                tenant_id=tenant_id,
                definition_id=wf_def.id,
                entity_type="exemption_grant",
                entity_id=new_record.id,
                current_step="submitted",
                status="initiated",
                history=[],
                context={},
            )
            self.db.add(workflow)

        # Step 7: Audit log (action in uppercase to pass CHECK constraint)
        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=user_id,
            action="SUBMIT_DOAP_SESSION",
            resource_type="doap_session_record",
            resource_id=new_record.id,
            new_values={
                "competency_code": data.competency_code,
                "stage": data.stage,
                "rating": data.rating,
                "faculty_decision": data.faculty_decision,
                "auto_logbook_entry_id": str(logbook_entry.id),
                "remediation_triggered": data.faculty_decision == "Re",
            },
        )

        await self.db.flush()
        return DoapSessionResponse.model_validate(new_record)

    async def get_doap_records(
        self,
        tenant_id: UUID,
        student_id: UUID,
        competency_code: str | None = None,
    ) -> list[DoapSessionResponse]:
        """List DOAP records for a student, optionally filtered by competency."""
        query = select(DoapSessionRecord).where(
            DoapSessionRecord.tenant_id == tenant_id,
            DoapSessionRecord.student_id == student_id,
            DoapSessionRecord.deleted_at.is_(None),
        )
        if competency_code:
            query = query.where(DoapSessionRecord.competency_code == competency_code)
        query = query.order_by(DoapSessionRecord.signed_off_at)

        result = await self.db.execute(query)
        records = result.scalars().all()
        return [DoapSessionResponse.model_validate(r) for r in records]

    async def compute_state(
        self,
        tenant_id: UUID,
        student_id: UUID,
        competency_code: str,
    ) -> DoapStateResponse:
        """Compute current DOAP state for a student + competency."""
        records_responses = await self.get_doap_records(tenant_id, student_id, competency_code)

        # compute_certified_stages expects ORM objects or dict-like, responses are Pydantic schemas which behave like objects
        certified = compute_certified_stages(records_responses)
        current = derive_current_state(certified)

        # Count records per stage
        records_per_stage = {"D": 0, "O": 0, "A": 0, "P": 0}
        for r in records_responses:
            records_per_stage[r.stage] = records_per_stage.get(r.stage, 0) + 1

        # Determine pending stage
        pending = None
        STAGE_ORDER = ["D", "O", "A", "P"]
        for s in STAGE_ORDER:
            if s not in certified:
                pending = s
                break

        return DoapStateResponse(
            student_id=student_id,
            competency_code=competency_code,
            current_state=current,
            records_per_stage=records_per_stage,
            certified_stages=sorted(certified, key=STAGE_ORDER.index),
            pending_stage=pending,
            last_record_at=records_responses[-1].signed_off_at if records_responses else None,
        )

    async def _infer_subject_code(self, tenant_id: UUID, competency_code: str) -> str:
        """Extract subject prefix from competency_code (e.g., AN1.1 -> ANAT)."""
        mdm = MdmConfigService(self.db)
        mapping = await mdm.get_subject_code_mapping(tenant_id)
        
        # Extract letters at start of competency_code
        prefix_chars = []
        for char in competency_code:
            if char.isalpha():
                prefix_chars.append(char)
            else:
                break
        prefix = "".join(prefix_chars).upper()

        subject_code = mapping.get(prefix)
        if not subject_code:
            import logging
            logging.warning("No subject_code mapping for prefix '%s'. Using 'UNKN'.", prefix)
        return subject_code or "UNKN"
