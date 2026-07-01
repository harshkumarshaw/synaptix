from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdmissionApplicationCreate(BaseModel):
    """Request to create an admission application."""

    application_number: str = Field(min_length=1, max_length=50)
    student_name: str = Field(min_length=1, max_length=150)
    applied_for_program_id: UUID


class AdmissionApplicationResponse(BaseModel):
    """Response serialisation for admission application."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_number: str
    student_name: str
    applied_for_program_id: UUID
    created_at: datetime
