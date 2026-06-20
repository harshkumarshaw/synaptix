from __future__ import annotations

import uuid
from typing import Optional
from sqlalchemy import ForeignKey, ForeignKeyConstraint, String, Text, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from packages.shared.db.base import TenantScopedBase
from app.models.course import Course
from app.models.curriculum import Curriculum

class LessonPlan(TenantScopedBase):
    __tablename__ = "lesson_plans"

    course_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    curriculum_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[int] = mapped_column(default=1, server_default="1", nullable=False)
    is_current: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)
    topic: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0, server_default="1.0", nullable=False)
    competency_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nmc_competency_level: Mapped[str] = mapped_column(String(2), nullable=False)
    is_core: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft", nullable=False)
    workflow_instance_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["workflow_instances.tenant_id", "workflow_instances.id"],
            ondelete="SET NULL"
        ),
    )

    course: Mapped[Course] = relationship("Course", lazy="raise")
    curriculum: Mapped[Curriculum] = relationship("Curriculum", lazy="raise", overlaps="course")
