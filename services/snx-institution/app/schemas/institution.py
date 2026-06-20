from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    code: str
    is_active: bool

    class Config:
        from_attributes = True


class FacultyResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    email: str | None
    department_id: uuid.UUID
    designation: str
    employee_id: str
    is_active: bool

    class Config:
        from_attributes = True


class StudentResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    email: str | None
    batch_id: uuid.UUID
    section_id: uuid.UUID | None
    roll_number: str
    admission_year: int
    status: str

    class Config:
        from_attributes = True


class StudentStatusUpdateRequest(BaseModel):
    status: str = Field(
        ..., description="New student status, e.g. detained, transferred, active, graduated"
    )
