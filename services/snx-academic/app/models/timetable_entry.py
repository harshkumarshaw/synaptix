from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.course import Course
from app.models.faculty import Faculty
from app.models.timetable_slot import TimetableSlot
from packages.shared.db.base import TenantScopedBase


class TimetableEntry(TenantScopedBase):
    __tablename__ = "timetable_entries"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("timetable_slots.id", ondelete="RESTRICT"), nullable=False
    )
    room_number: Mapped[str | None] = mapped_column(nullable=True)

    # Relationships
    slot: Mapped[TimetableSlot] = relationship("TimetableSlot", lazy="raise")
    course: Mapped[Course] = relationship("Course", lazy="raise")
    faculty: Mapped[Faculty] = relationship("Faculty", lazy="raise")
