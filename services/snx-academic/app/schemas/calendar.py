from __future__ import annotations

import uuid
import datetime
from typing import Optional, List
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
    description: Optional[str] = None
    event_type: str = Field(..., description="lecture, practical, doap, ece, clinical_posting, foundation_course, aetcom, examination")
    professional_phase: str = Field(..., description="Phase I, Phase II, Phase III Part I, Phase III Part II")
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    courses: List[EventCourseBase]
    assigned_faculty: List[EventFacultyBase]

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    event_type: Optional[str] = None
    professional_phase: Optional[str] = None
    date: Optional[datetime.date] = None
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    status: Optional[str] = None
    parent_event_id: Optional[uuid.UUID] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[uuid.UUID] = None

class EventResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    batch_id: uuid.UUID
    academic_year_id: uuid.UUID
    title: str
    description: Optional[str]
    event_type: str
    attendance_category: str
    professional_phase: str
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    status: str
    parent_event_id: Optional[uuid.UUID]
    cancellation_reason: Optional[str]
    cancelled_by: Optional[uuid.UUID]
    courses: List[EventCourseResponse]
    assigned_faculty: List[EventFacultyResponse]

    class Config:
        from_attributes = True
