from __future__ import annotations

import uuid
from datetime import time

from pydantic import BaseModel


class ProgramResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    code: str
    type: str
    duration_years: int
    is_active: bool

    class Config:
        from_attributes = True


class CourseResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    curriculum_id: uuid.UUID
    name: str
    code: str
    department_id: uuid.UUID
    is_active: bool
    default_attendance_category: str

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    academic_year_id: uuid.UUID
    program_id: uuid.UUID
    name: str
    code: str
    is_active: bool

    class Config:
        from_attributes = True


class TimetableSlotResponse(BaseModel):
    id: uuid.UUID
    day_of_week: int
    start_time: time
    end_time: time
    name: str | None

    class Config:
        from_attributes = True


class TimetableEntryResponse(BaseModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    course_id: uuid.UUID
    course_code: str
    course_name: str
    faculty_id: uuid.UUID
    faculty_name: str
    slot: TimetableSlotResponse
    room_number: str | None

    class Config:
        from_attributes = True
