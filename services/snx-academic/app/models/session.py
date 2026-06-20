from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, ForeignKeyConstraint, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.calendar import Event
from app.models.lesson_plan import LessonPlan
from packages.shared.db.base import TenantScopedBase


class Session(TenantScopedBase):
    __tablename__ = "sessions"

    event_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    lesson_plan_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    session_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    conducted_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False
    )
    actual_hours: Mapped[float] = mapped_column(
        Numeric(4, 2), default=1.0, server_default="1.0", nullable=False
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "event_id"], ["events.tenant_id", "events.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "lesson_plan_id"],
            ["lesson_plans.tenant_id", "lesson_plans.id"],
            ondelete="RESTRICT",
        ),
    )

    event: Mapped[Event] = relationship("Event", lazy="raise")
    lesson_plan: Mapped[LessonPlan | None] = relationship(
        "LessonPlan", lazy="raise", overlaps="event"
    )
    conducted_faculty: Mapped[list[SessionFaculty]] = relationship(
        "SessionFaculty", back_populates="session", lazy="raise"
    )


class SessionFaculty(TenantScopedBase):
    __tablename__ = "session_faculty"

    session_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    faculty_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "session_id"], ["sessions.tenant_id", "sessions.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "faculty_id"], ["faculty.tenant_id", "faculty.id"], ondelete="RESTRICT"
        ),
    )

    session: Mapped[Session] = relationship(
        "Session", back_populates="conducted_faculty", lazy="raise"
    )
