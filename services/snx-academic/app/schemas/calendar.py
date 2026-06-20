from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, Field


class EventFacultyBase(BaseModel):
    faculty_id: uuid.UUID


class EventFacultyResponse(EventFacultyBase):
    tenant_id: uuid.UUID
    event_id: uuid.UUID

    class Config:
        from_attributes = True


class EventCourseBase(BaseModel):
    course_id: uuid.UUID
    is_primary: bool = False


class EventCourseResponse(EventCourseBase):
    tenant_id: uuid.UUID
    event_id: uuid.UUID

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    batch_id: uuid.UUID
    academic_year_id: uuid.UUID
    title: str = Field(..., max_length=150)
    description: str | None = None
    event_type: str = Field(
        ...,
        description="lecture, practical, doap, ece, clinical_posting, foundation_course, aetcom, examination",
    )
    professional_phase: str = Field(
        ..., description="Phase I, Phase II, Phase III Part I, Phase III Part II"
    )
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    courses: list[EventCourseBase]
    assigned_faculty: list[EventFacultyBase]


class EventUpdate(BaseModel):
    title: str | None = Field(None, max_length=150)
    description: str | None = None
    event_type: str | None = None
    professional_phase: str | None = None
    date: datetime.date | None = None
    start_time: datetime.time | None = None
    end_time: datetime.time | None = None
    status: str | None = None
    parent_event_id: uuid.UUID | None = None
    cancellation_reason: str | None = None
    cancelled_by: uuid.UUID | None = None


class EventResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    batch_id: uuid.UUID
    academic_year_id: uuid.UUID
    title: str
    description: str | None
    event_type: str
    attendance_category: str
    professional_phase: str
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    status: str
    parent_event_id: uuid.UUID | None
    cancellation_reason: str | None
    cancelled_by: uuid.UUID | None
    courses: list[EventCourseResponse]
    assigned_faculty: list[EventFacultyResponse]

    class Config:
        from_attributes = True
