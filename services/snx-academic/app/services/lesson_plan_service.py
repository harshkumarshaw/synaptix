from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends

# Stub imports or raw table queries to interact with snx-workflow tables
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson_plan import LessonPlan
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanUpdate
from app.services.audit_logger import write_audit_log
from packages.shared.db.session import get_db
from packages.shared.errors import (
    DuplicateRecordError,
    ResourceNotFoundError,
    ValidationError,
)
from packages.shared.logging import get_logger

logger = get_logger(__name__)


class LessonPlanService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def create_lesson_plan(
        self, tenant_id: uuid.UUID, lp_in: LessonPlanCreate, actor_id: uuid.UUID | None = None
    ) -> LessonPlan:
        # Check if a current lesson plan with this code already exists for the course/curriculum
        stmt = select(LessonPlan).where(
            LessonPlan.tenant_id == tenant_id,
            LessonPlan.course_id == lp_in.course_id,
            LessonPlan.curriculum_id == lp_in.curriculum_id,
            LessonPlan.code == lp_in.code,
            LessonPlan.is_current,
            LessonPlan.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise DuplicateRecordError(
                f"A current lesson plan with code '{lp_in.code}' already exists for this course and curriculum."
            )

        lp = LessonPlan(
            tenant_id=tenant_id,
            course_id=lp_in.course_id,
            curriculum_id=lp_in.curriculum_id,
            code=lp_in.code,
            version=1,
            is_current=True,
            topic=lp_in.topic,
            description=lp_in.description,
            estimated_hours=lp_in.estimated_hours,
            competency_code=lp_in.competency_code,
            nmc_competency_level=lp_in.nmc_competency_level,
            is_core=lp_in.is_core,
            status="draft",
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(lp)
        try:
            await self.db.flush()
        except IntegrityError as e:
            raise DuplicateRecordError("Unique constraint violation creating lesson plan") from e

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="CREATE",
            resource_type="lesson_plan",
            resource_id=lp.id,
            new_values={
                "code": lp.code,
                "course_id": str(lp.course_id),
                "curriculum_id": str(lp.curriculum_id),
                "version": lp.version,
            },
        )

        return lp

    async def get_lesson_plan(self, tenant_id: uuid.UUID, lp_id: uuid.UUID) -> LessonPlan:
        stmt = select(LessonPlan).where(
            LessonPlan.tenant_id == tenant_id,
            LessonPlan.id == lp_id,
            LessonPlan.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        lp = res.scalar_one_or_none()
        if not lp:
            raise ResourceNotFoundError(f"LessonPlan with ID {lp_id} not found.")
        return lp

    async def update_lesson_plan(
        self,
        tenant_id: uuid.UUID,
        lp_id: uuid.UUID,
        lp_in: LessonPlanUpdate,
        actor_id: uuid.UUID | None = None,
    ) -> LessonPlan:
        lp = await self.get_lesson_plan(tenant_id, lp_id)

        # If the lesson plan is currently in draft, we can update it in-place
        if lp.status == "draft":
            update_data = lp_in.model_dump(exclude_unset=True)
            for field, val in update_data.items():
                setattr(lp, field, val)
            lp.updated_by = actor_id
            await self.db.flush()

            await write_audit_log(
                db=self.db,
                tenant_id=tenant_id,
                actor_user_id=actor_id,
                action="UPDATE",
                resource_type="lesson_plan",
                resource_id=lp.id,
                new_values=update_data,
            )
            return lp

        # If it is NOT in draft (e.g. pending_approval, approved, rejected), we must spawn a new version
        # Step 1: Deactivate the old version (set is_current = False)
        lp.is_current = False
        lp.updated_by = actor_id
        await self.db.flush()

        # Step 2: Create new version record
        new_version = lp.version + 1

        # Merge old values with new updates
        lp_dict = {
            "topic": lp.topic,
            "description": lp.description,
            "estimated_hours": lp.estimated_hours,
            "competency_code": lp.competency_code,
            "nmc_competency_level": lp.nmc_competency_level,
            "is_core": lp.is_core,
        }
        update_data = lp_in.model_dump(exclude_unset=True)
        lp_dict.update(update_data)

        new_lp = LessonPlan(
            tenant_id=tenant_id,
            course_id=lp.course_id,
            curriculum_id=lp.curriculum_id,
            code=lp.code,
            version=new_version,
            is_current=True,
            topic=lp_dict["topic"],
            description=lp_dict["description"],
            estimated_hours=lp_dict["estimated_hours"],
            competency_code=lp_dict["competency_code"],
            nmc_competency_level=lp_dict["nmc_competency_level"],
            is_core=lp_dict["is_core"],
            status="draft",  # Newly created version starts as draft
            created_by=actor_id,
            updated_by=actor_id,
        )

        self.db.add(new_lp)
        try:
            await self.db.flush()
        except IntegrityError as e:
            raise DuplicateRecordError(
                "Unique constraint violation during lesson plan versioning"
            ) from e

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="CREATE_VERSION",
            resource_type="lesson_plan",
            resource_id=new_lp.id,
            new_values={"code": new_lp.code, "version": new_lp.version, "parent_id": str(lp.id)},
        )

        return new_lp

    async def submit_for_approval(
        self, tenant_id: uuid.UUID, lp_id: uuid.UUID, actor_id: uuid.UUID | None = None
    ) -> LessonPlan:
        lp = await self.get_lesson_plan(tenant_id, lp_id)
        if not lp.is_current:
            raise ValidationError("Cannot submit a non-current lesson plan version for approval.")

        if lp.status not in ("draft", "rejected"):
            raise ValidationError(
                f"Cannot submit lesson plan for approval from status '{lp.status}'."
            )

        # Query the workflow_definitions table to find the active "lesson_plan_approval" workflow
        wfd_stmt = text(
            "SELECT id, steps FROM workflow_definitions "
            "WHERE tenant_id = :tenant_id AND code = :code AND is_current = TRUE AND deleted_at IS NULL"
        )
        wfd_res = await self.db.execute(
            wfd_stmt, {"tenant_id": tenant_id, "code": "lesson_plan_approval"}
        )
        wfd = wfd_res.first()
        if not wfd:
            raise ResourceNotFoundError(
                "Active workflow definition 'lesson_plan_approval' not found."
            )

        definition_id, steps = wfd
        initial_step = "hod_review"  # Fallback standard initial step
        required_role = "HOD"
        if steps and isinstance(steps, dict):
            # Try to resolve initial step from definition steps if present
            # Usually the workflow definition has a list of steps or a specific initial key
            for step_key, step_val in steps.items():
                if isinstance(step_val, dict):
                    # Check if this step is initial or just pick hod_review
                    if step_key == "hod_review":
                        initial_step = step_key
                        required_role = step_val.get("required_role", "HOD")
                        break

        # Check if an active workflow instance already exists for this lesson_plan
        wfi_check_stmt = text(
            "SELECT id FROM workflow_instances "
            "WHERE tenant_id = :tenant_id AND entity_type = :entity_type AND entity_id = :entity_id "
            "AND status NOT IN ('approved', 'rejected', 'cancelled') AND deleted_at IS NULL"
        )
        wfi_check_res = await self.db.execute(
            wfi_check_stmt,
            {"tenant_id": tenant_id, "entity_type": "lesson_plan_approval", "entity_id": lp_id},
        )
        existing_wfi = wfi_check_res.first()
        if existing_wfi:
            raise ValidationError(
                "An active workflow instance already exists for this lesson plan."
            )

        # Create a new workflow instance row directly in workflow_instances table
        wfi_id = uuid.uuid4()
        now = datetime.now(UTC)
        due_at = now + timedelta(days=2)  # Default SLA: 2 days

        wfi_insert_stmt = text(
            "INSERT INTO workflow_instances (id, tenant_id, definition_id, entity_type, entity_id, "
            "current_step, status, current_assignee_role, due_at, history, context, created_at, updated_at) "
            "VALUES (:id, :tenant_id, :definition_id, :entity_type, :entity_id, "
            ":current_step, :status, :current_assignee_role, :due_at, '[]'::jsonb, :context, :now, :now)"
        )

        # Populate context snapshot with static lesson plan data for approval
        context_data = {
            "topic": lp.topic,
            "description": lp.description,
            "estimated_hours": float(lp.estimated_hours),
            "competency_code": lp.competency_code,
            "nmc_competency_level": lp.nmc_competency_level,
            "is_core": lp.is_core,
            "code": lp.code,
            "version": lp.version,
        }

        import json

        await self.db.execute(
            wfi_insert_stmt,
            {
                "id": wfi_id,
                "tenant_id": tenant_id,
                "definition_id": definition_id,
                "entity_type": "lesson_plan_approval",
                "entity_id": lp_id,
                "current_step": initial_step,
                "status": "pending",
                "current_assignee_role": required_role,
                "due_at": due_at,
                "context": json.dumps(context_data),
                "now": now,
            },
        )

        # Update lesson plan status and link workflow_instance_id
        lp.status = "pending_approval"
        lp.workflow_instance_id = wfi_id
        lp.updated_by = actor_id
        await self.db.flush()

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="SUBMIT_APPROVAL",
            resource_type="lesson_plan",
            resource_id=lp.id,
            new_values={"status": lp.status, "workflow_instance_id": str(wfi_id)},
        )

        return lp
