"""
Pydantic v2 schemas — Leave Management (Phase 2).

All schemas use strict mode. No `any` types.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LeaveRequestCreate(BaseModel):
    """Create a leave request. Student-facing endpoint."""

    leave_type: Literal["medical", "academic", "casual", "other"]
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=10, max_length=2000)
    rotation_id: uuid.UUID | None = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info: object) -> date:
        """Validate end date is not before start date."""
        start = getattr(info, "data", {}).get("start_date")
        if start and v < start:
            raise ValueError("end_date must be on or after start_date")
        return v


class LeaveApproveRequest(BaseModel):
    """Approve a leave request. HOD/Principal-facing endpoint."""

    remarks: str | None = Field(None, max_length=500)


class LeaveRejectRequest(BaseModel):
    """Reject a leave request."""

    remarks: str = Field(..., min_length=5, max_length=500)


class LeaveRequestOut(BaseModel):
    """Leave request response schema."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    status: str
    workflow_instance_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
