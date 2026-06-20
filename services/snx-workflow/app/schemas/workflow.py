from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class WorkflowStepItem(BaseModel):
    name: str
    required_role: str
    next_steps: list[str]


class WorkflowDefinitionBase(BaseModel):
    name: str
    code: str
    description: str | None = None
    steps: dict[str, WorkflowStepItem]
    is_active: bool = True


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: dict[str, WorkflowStepItem]) -> dict[str, WorkflowStepItem]:
        # Validate that terminal steps (e.g., 'approved', 'rejected', 'cancelled')
        # exist or that transitions form a valid graph (no invalid next steps)
        for step_name, step_item in v.items():
            for next_step in step_item.next_steps:
                if next_step not in v and next_step not in ("approved", "rejected", "cancelled"):
                    raise ValueError(
                        f"Step '{step_name}' has invalid transition target '{next_step}'"
                    )
        return v


class WorkflowDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    code: str
    description: str | None
    version: int
    is_current: bool
    steps: dict[str, WorkflowStepItem]
    is_active: bool


class WorkflowInstanceCreate(BaseModel):
    definition_code: str  # We resolve to the is_current version definition
    entity_type: str
    entity_id: uuid.UUID
    context: dict[str, Any]  # Snapshot of current state (static)
    initial_step: str = "start"


class WorkflowInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    definition_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    current_step: str
    status: str
    current_assignee_id: uuid.UUID | None
    current_assignee_role: str | None
    due_at: datetime | None
    history: list[dict[str, Any]]
    context: dict[str, Any]


class WorkflowTransitionCreate(BaseModel):
    to_step: str
    comment: str | None = None
    # actor_id is extracted from JWT user context
