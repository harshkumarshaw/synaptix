from __future__ import annotations

import uuid
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

class LessonPlanBase(BaseModel):
    topic: str = Field(..., max_length=150)
    description: Optional[str] = None
    estimated_hours: float = Field(1.0, ge=0.25, le=100.0)
    competency_code: Optional[str] = Field(None, max_length=50)
    nmc_competency_level: str = Field(..., description="K, KH, SH, P")
    is_core: bool = False

    @field_validator("nmc_competency_level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        if v not in ("K", "KH", "SH", "P"):
            raise ValueError("nmc_competency_level must be one of K, KH, SH, P")
        return v

class LessonPlanCreate(LessonPlanBase):
    course_id: uuid.UUID
    curriculum_id: uuid.UUID
    code: str = Field(..., description="Unique alphanumeric code scoped per course")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not re.match(r"^[A-Z0-9_.-]{3,50}$", v):
            raise ValueError("code must be alphanumeric (allowing dots, dashes, underscores) and between 3 to 50 characters")
        return v

class LessonPlanUpdate(BaseModel):
    topic: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0.25, le=100.0)
    competency_code: Optional[str] = Field(None, max_length=50)
    nmc_competency_level: Optional[str] = None
    is_core: Optional[bool] = None

class LessonPlanResponse(LessonPlanBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    course_id: uuid.UUID
    curriculum_id: uuid.UUID
    code: str
    version: int
    is_current: bool
    status: str
    workflow_instance_id: Optional[uuid.UUID]

    class Config:
        from_attributes = True
