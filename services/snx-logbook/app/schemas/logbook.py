from __future__ import annotations

import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class FoundationCourseRecordResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    module_name: str
    completed_hours: float
    required_hours: float
    is_completed: bool
    signoff_received_at: Optional[datetime.datetime]
    signed_off_by: Optional[uuid.UUID]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class FoundationCourseHoursLog(BaseModel):
    student_id: uuid.UUID
    module_name: str
    hours: float = Field(..., ge=0.0, le=100.0)

    @field_validator("module_name")
    @classmethod
    def validate_module(cls, v: str) -> str:
        valid = ('orientation', 'skills_acquisition', 'professional_development', 'language_computer', 'sports_yoga', 'hospital_visits')
        if v not in valid:
            raise ValueError(f"module_name must be one of {valid}")
        return v


class FoundationCourseSignoffPayload(BaseModel):
    student_id: uuid.UUID
    module_name: str

    @field_validator("module_name")
    @classmethod
    def validate_module(cls, v: str) -> str:
        valid = ('orientation', 'skills_acquisition', 'professional_development', 'language_computer', 'sports_yoga', 'hospital_visits')
        if v not in valid:
            raise ValueError(f"module_name must be one of {valid}")
        return v


class AetcomReflectionSubmit(BaseModel):
    module_code: str = Field(..., max_length=30)
    competency_code: str = Field(..., max_length=50)
    professional_phase: str
    reflection_text: str

    @field_validator("professional_phase")
    @classmethod
    def validate_phase(cls, v: str) -> str:
        valid = ('Phase I', 'Phase II', 'Phase III Part I', 'Phase III Part II')
        if v not in valid:
            raise ValueError(f"professional_phase must be one of {valid}")
        return v


class AetcomSignoffPayload(BaseModel):
    student_id: uuid.UUID
    module_code: str = Field(..., max_length=30)
    competency_code: str = Field(..., max_length=50)
    professional_phase: str

    @field_validator("professional_phase")
    @classmethod
    def validate_phase(cls, v: str) -> str:
        valid = ('Phase I', 'Phase II', 'Phase III Part I', 'Phase III Part II')
        if v not in valid:
            raise ValueError(f"professional_phase must be one of {valid}")
        return v


class AetcomRecordResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    module_code: str
    competency_code: str
    professional_phase: str
    status: str
    reflection_text: Optional[str]
    signed_off_by: Optional[uuid.UUID]
    signed_off_at: Optional[datetime.datetime]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
