from __future__ import annotations

import uuid
import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator

class SessionFacultyBase(BaseModel):
    faculty_id: uuid.UUID

class SessionFacultyResponse(SessionFacultyBase):
    tenant_id: uuid.UUID
    session_id: uuid.UUID

    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    event_id: uuid.UUID
    lesson_plan_id: Optional[uuid.UUID] = None
    session_reason: Optional[str] = None
    conducted_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    actual_hours: float = Field(1.0, ge=0.25, le=100.0)
    remarks: Optional[str] = None
    conducted_faculty: List[SessionFacultyBase]

    @model_validator(mode="after")
    def validate_reason_when_no_plan(self) -> SessionCreate:
        if self.lesson_plan_id is None and not self.session_reason:
            raise ValueError("session_reason is required if lesson_plan_id is null")
        return self

class SessionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    event_id: uuid.UUID
    lesson_plan_id: Optional[uuid.UUID]
    session_reason: Optional[str]
    conducted_at: datetime.datetime
    actual_hours: float
    remarks: Optional[str]
    conducted_faculty: List[SessionFacultyResponse]

    class Config:
        from_attributes = True
