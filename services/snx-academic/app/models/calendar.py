from __future__ import annotations

import datetime
import uuid
from typing import Optional, List
from sqlalchemy import ForeignKey, ForeignKeyConstraint, Date, Time, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from packages.shared.db.base import TenantScopedBase
from app.models.batch import Batch
from app.models.academic_year import AcademicYear

class Event(TenantScopedBase):
    __tablename__ = "events"

    batch_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    attendance_category: Mapped[str] = mapped_column(String(30), nullable=False)
    professional_phase: Mapped[str] = mapped_column(String(20), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="scheduled", server_default="scheduled")
    parent_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    
    # Denormalized audit columns
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["batches.tenant_id", "batches.id"],
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "parent_event_id"],
            ["events.tenant_id", "events.id"],
            ondelete="SET NULL"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "cancelled_by"],
            ["users.tenant_id", "users.id"],
            ondelete="SET NULL"
        ),
    )

    batch: Mapped[Batch] = relationship("Batch", lazy="raise")
    academic_year: Mapped[AcademicYear] = relationship("AcademicYear", lazy="raise", overlaps="batch")
    courses: Mapped[List[EventCourse]] = relationship("EventCourse", back_populates="event", lazy="raise")
    assigned_faculty: Mapped[List[EventFaculty]] = relationship("EventFaculty", back_populates="event", lazy="raise")


class EventFaculty(TenantScopedBase):
    __tablename__ = "event_faculty"

    event_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    faculty_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "event_id"],
            ["events.tenant_id", "events.id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "faculty_id"],
            ["faculty.tenant_id", "faculty.id"],
            ondelete="RESTRICT"
        ),
    )

    event: Mapped[Event] = relationship("Event", back_populates="assigned_faculty", lazy="raise")


class EventCourse(TenantScopedBase):
    __tablename__ = "event_courses"

    event_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False, server_default="false")

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "event_id"],
            ["events.tenant_id", "events.id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT"
        ),
    )

    event: Mapped[Event] = relationship("Event", back_populates="courses", lazy="raise")
