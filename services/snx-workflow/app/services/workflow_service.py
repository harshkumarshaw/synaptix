from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional, Any
from fastapi import Depends
from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from packages.shared.db.session import get_db
from packages.shared.errors import (
    ResourceNotFoundError,
    ValidationError,
    DuplicateRecordError,
    PermissionDeniedError,
    InvalidStateTransitionError,
)
from packages.shared.logging import get_logger
from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowTransition
from app.models.user import User
from app.schemas.workflow import WorkflowDefinitionCreate, WorkflowInstanceCreate

logger = get_logger(__name__)


class WorkflowService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def get_definitions(self, tenant_id: uuid.UUID) -> list[WorkflowDefinition]:
        stmt = select(WorkflowDefinition).where(
            WorkflowDefinition.tenant_id == tenant_id,
            WorkflowDefinition.deleted_at.is_(None)
        ).order_by(WorkflowDefinition.code, WorkflowDefinition.version)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_definition(self, tenant_id: uuid.UUID, definition_id: uuid.UUID) -> WorkflowDefinition:
        stmt = select(WorkflowDefinition).where(
            WorkflowDefinition.tenant_id == tenant_id,
            WorkflowDefinition.id == definition_id,
            WorkflowDefinition.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        definition = res.scalar_one_or_none()
        if not definition:
            raise ResourceNotFoundError(f"WorkflowDefinition {definition_id} not found")
        return definition

    async def get_current_definition_by_code(self, tenant_id: uuid.UUID, code: str) -> WorkflowDefinition:
        stmt = select(WorkflowDefinition).where(
            WorkflowDefinition.tenant_id == tenant_id,
            WorkflowDefinition.code == code,
            WorkflowDefinition.is_current == True,
            WorkflowDefinition.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        definition = res.scalar_one_or_none()
        if not definition:
            raise ResourceNotFoundError(f"Active WorkflowDefinition for code '{code}' not found")
        return definition

    async def create_definition(
        self, tenant_id: uuid.UUID, schema: WorkflowDefinitionCreate
    ) -> WorkflowDefinition:
        # Determine the next version
        stmt = select(func.max(WorkflowDefinition.version)).where(
            WorkflowDefinition.tenant_id == tenant_id,
            WorkflowDefinition.code == schema.code
        )
        res = await self.db.execute(stmt)
        max_ver = res.scalar() or 0
        next_ver = max_ver + 1

        # Deactivate previous versions atomically
        await self.db.execute(
            update(WorkflowDefinition)
            .where(
                WorkflowDefinition.tenant_id == tenant_id,
                WorkflowDefinition.code == schema.code,
                WorkflowDefinition.is_current == True
            )
            .values(is_current=False)
        )

        steps_dict = {k: v.model_dump() for k, v in schema.steps.items()}

        definition = WorkflowDefinition(
            tenant_id=tenant_id,
            name=schema.name,
            code=schema.code,
            description=schema.description,
            version=next_ver,
            is_current=True,
            steps=steps_dict,
            is_active=schema.is_active,
        )
        self.db.add(definition)
        try:
            await self.db.commit()
            await self.db.refresh(definition)
        except IntegrityError as e:
            await self.db.rollback()
            raise DuplicateRecordError("Unique constraint violation creating definition") from e

        return definition

    async def create_instance(
        self, tenant_id: uuid.UUID, schema: WorkflowInstanceCreate
    ) -> WorkflowInstance:
        # Resolve active definition
        definition = await self.get_current_definition_by_code(tenant_id, schema.definition_code)

        # Check for active instance limit (status NOT IN ('approved', 'rejected', 'cancelled'))
        stmt = select(WorkflowInstance).where(
            WorkflowInstance.tenant_id == tenant_id,
            WorkflowInstance.entity_type == schema.entity_type,
            WorkflowInstance.entity_id == schema.entity_id,
            WorkflowInstance.status.notin_(("approved", "rejected", "cancelled")),
            WorkflowInstance.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise ValidationError(
                f"An active workflow instance already exists for entity {schema.entity_type} {schema.entity_id}"
            )

        # Resolve first step details
        steps = definition.steps
        initial_step_name = schema.initial_step
        if initial_step_name not in steps:
            raise ValidationError(f"Initial step '{initial_step_name}' not defined in workflow")

        initial_step = steps[initial_step_name]
        required_role = initial_step.get("required_role")

        instance = WorkflowInstance(
            tenant_id=tenant_id,
            definition_id=definition.id,
            entity_type=schema.entity_type,
            entity_id=schema.entity_id,
            current_step=initial_step_name,
            status="pending",
            current_assignee_role=required_role,
            due_at=datetime.now(timezone.utc) + timedelta(days=2),  # Default 48h SLA
            context=schema.context,
            history=[],
        )
        self.db.add(instance)
        try:
            await self.db.commit()
            await self.db.refresh(instance)
        except IntegrityError as e:
            await self.db.rollback()
            raise DuplicateRecordError("Unique constraint violation creating instance") from e

        return instance

    async def get_instance(self, tenant_id: uuid.UUID, instance_id: uuid.UUID) -> WorkflowInstance:
        stmt = select(WorkflowInstance).where(
            WorkflowInstance.tenant_id == tenant_id,
            WorkflowInstance.id == instance_id,
            WorkflowInstance.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        instance = res.scalar_one_or_none()
        if not instance:
            raise ResourceNotFoundError(f"WorkflowInstance {instance_id} not found")
        return instance

    async def submit_transition(
        self,
        tenant_id: uuid.UUID,
        instance_id: uuid.UUID,
        to_step: str,
        comment: Optional[str],
        actor_user_id: uuid.UUID,
        actor_roles: list[str],
    ) -> WorkflowInstance:
        # Lock row for updates to handle concurrency
        stmt = (
            select(WorkflowInstance)
            .where(
                WorkflowInstance.tenant_id == tenant_id,
                WorkflowInstance.id == instance_id,
                WorkflowInstance.deleted_at.is_(None)
            )
            .with_for_update()
        )
        res = await self.db.execute(stmt)
        instance = res.scalar_one_or_none()
        if not instance:
            raise ResourceNotFoundError(f"WorkflowInstance {instance_id} not found")

        # Resolve definition
        definition = await self.get_definition(tenant_id, instance.definition_id)
        steps = definition.steps
        current_step_name = instance.current_step

        if current_step_name not in steps:
            raise ValidationError(f"Current step '{current_step_name}' not defined in workflow definition")

        current_step_def = steps[current_step_name]
        allowed_next = current_step_def.get("next_steps", [])

        if to_step not in allowed_next:
            raise InvalidStateTransitionError(f"Transition from '{current_step_name}' to '{to_step}' is invalid")

        # Verify role permission
        # The actor must possess the role required for the step they are acting on
        required_role = current_step_def.get("required_role")
        if required_role and required_role not in actor_roles and "super_admin" not in actor_roles:
            raise PermissionDeniedError(f"Actor lacks required role '{required_role}' for this transition")

        # If next step is terminal
        if to_step in ("approved", "rejected", "cancelled"):
            instance.current_step = to_step
            instance.status = to_step
            instance.current_assignee_id = None
            instance.current_assignee_role = None
            instance.due_at = None
        else:
            if to_step not in steps:
                raise ValidationError(f"Target step '{to_step}' not defined in workflow definition")

            next_step_def = steps[to_step]
            instance.current_step = to_step
            instance.status = "pending"
            instance.current_assignee_role = next_step_def.get("required_role")
            instance.due_at = datetime.now(timezone.utc) + timedelta(days=2)  # Reset SLA

            # Soft-deleted assignee check (AUDIT-O1)
            # If current assignee is set but soft deleted, clear it to fall back to role assignment
            if instance.current_assignee_id:
                assignee_stmt = select(User).where(
                    User.tenant_id == tenant_id,
                    User.id == instance.current_assignee_id
                )
                a_res = await self.db.execute(assignee_stmt)
                assignee = a_res.scalar_one_or_none()
                if assignee and assignee.deleted_at is not None:
                    logger.warning(
                        "Assignee is soft-deleted. Reassigning workflow to HOD/role defaults.",
                        extra={"instance_id": str(instance.id), "user_id": str(assignee.id)},
                    )
                    instance.current_assignee_id = None

        # Insert transition record
        # This will fire the AFTER INSERT trigger to append to instance.history JSONB cache atomically
        transition = WorkflowTransition(
            tenant_id=tenant_id,
            instance_id=instance.id,
            from_step=current_step_name,
            to_step=to_step,
            actor_id=actor_user_id,
            comment=comment,
        )
        self.db.add(transition)

        # Write to global audit log
        from app.services.audit_logger import write_audit_log
        await write_audit_log(
            self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="WORKFLOW_TRANSITION",
            resource_type="workflow_instance",
            resource_id=instance.id,
            old_values={"current_step": current_step_name, "status": instance.status},
            new_values={"current_step": to_step, "status": instance.status},
        )

        try:
            await self.db.commit()
            await self.db.refresh(instance)
        except Exception as e:
            await self.db.rollback()
            raise ValidationError("Failed to record workflow transition") from e

        return instance
