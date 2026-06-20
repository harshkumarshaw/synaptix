from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional
from fastapi import Depends
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.db.session import get_db
from packages.shared.errors import (
    ResourceNotFoundError,
    ValidationError,
)
from packages.shared.logging import get_logger
from app.models.session import Session, SessionFaculty
from app.models.calendar import Event
from app.models.lesson_plan import LessonPlan
from app.schemas.session import SessionCreate
from app.services.audit_logger import write_audit_log

logger = get_logger(__name__)


class SessionTrackingService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def conduct_session(
        self, tenant_id: uuid.UUID, session_in: SessionCreate, actor_id: Optional[uuid.UUID] = None
    ) -> Session:
        # Check event existence
        event_stmt = select(Event).where(Event.tenant_id == tenant_id, Event.id == session_in.event_id)
        res = await self.db.execute(event_stmt)
        event = res.scalar_one_or_none()
        if not event:
            raise ResourceNotFoundError(f"Event with ID {session_in.event_id} not found.")

        # Check if session is already recorded for this event
        existing_stmt = select(Session).where(Session.tenant_id == tenant_id, Session.event_id == session_in.event_id)
        existing_res = await self.db.execute(existing_stmt)
        if existing_res.scalar_one_or_none():
            raise ValidationError(f"A session has already been recorded for event {session_in.event_id}.")

        # Check lesson plan existence and validate unplanned session reason
        if session_in.lesson_plan_id:
            lp_stmt = select(LessonPlan).where(
                LessonPlan.tenant_id == tenant_id,
                LessonPlan.id == session_in.lesson_plan_id,
                LessonPlan.deleted_at.is_(None)
            )
            lp_res = await self.db.execute(lp_stmt)
            lp = lp_res.scalar_one_or_none()
            if not lp:
                raise ResourceNotFoundError(f"LessonPlan with ID {session_in.lesson_plan_id} not found.")
        else:
            if not session_in.session_reason or not session_in.session_reason.strip():
                raise ValidationError("session_reason is required for unplanned sessions (when lesson_plan_id is null).")

        # Update event status to 'conducted'
        event.status = "conducted"
        event.updated_by = actor_id
        await self.db.flush()

        # Create Session
        session = Session(
            tenant_id=tenant_id,
            event_id=session_in.event_id,
            lesson_plan_id=session_in.lesson_plan_id,
            session_reason=session_in.session_reason,
            conducted_at=session_in.conducted_at or datetime.now(timezone.utc),
            actual_hours=session_in.actual_hours,
            remarks=session_in.remarks,
            created_by=actor_id,
            updated_by=actor_id
        )
        self.db.add(session)
        await self.db.flush()

        # Add assigned faculty
        for fac_item in session_in.conducted_faculty:
            sf = SessionFaculty(
                tenant_id=tenant_id,
                session_id=session.id,
                faculty_id=fac_item.faculty_id
            )
            self.db.add(sf)

        await self.db.flush()

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="CONDUCT_SESSION",
            resource_type="session",
            resource_id=session.id,
            new_values={
                "event_id": str(session.event_id),
                "lesson_plan_id": str(session.lesson_plan_id) if session.lesson_plan_id else None,
                "actual_hours": float(session.actual_hours)
            }
        )

        return session

    async def get_session(self, tenant_id: uuid.UUID, session_id: uuid.UUID) -> Session:
        stmt = (
            select(Session)
            .options(selectinload(Session.conducted_faculty))
            .where(Session.tenant_id == tenant_id, Session.id == session_id)
        )
        res = await self.db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise ResourceNotFoundError(f"Session with ID {session_id} not found.")
        return session

    async def calculate_syllabus_coverage(
        self, tenant_id: uuid.UUID, course_id: uuid.UUID, curriculum_id: uuid.UUID
    ) -> dict:
        # 1. Competency Coverage (Primary Metric)
        # Total core competencies defined in lesson plans
        stmt_total_comp = (
            select(func.count(func.distinct(LessonPlan.competency_code)))
            .where(
                LessonPlan.tenant_id == tenant_id,
                LessonPlan.course_id == course_id,
                LessonPlan.curriculum_id == curriculum_id,
                LessonPlan.is_core == True,
                LessonPlan.competency_code.is_not(None),
                LessonPlan.is_current == True,
                LessonPlan.deleted_at.is_(None)
            )
        )
        total_comp_res = await self.db.execute(stmt_total_comp)
        total_core_comp = total_comp_res.scalar() or 0

        # Conducted core competencies
        stmt_conducted_comp = (
            select(func.count(func.distinct(LessonPlan.competency_code)))
            .select_from(Session)
            .join(LessonPlan, Session.lesson_plan_id == LessonPlan.id)
            .where(
                Session.tenant_id == tenant_id,
                LessonPlan.course_id == course_id,
                LessonPlan.curriculum_id == curriculum_id,
                LessonPlan.is_core == True,
                LessonPlan.competency_code.is_not(None),
                LessonPlan.deleted_at.is_(None)
            )
        )
        conducted_comp_res = await self.db.execute(stmt_conducted_comp)
        conducted_core_comp = conducted_comp_res.scalar() or 0

        competency_coverage = (
            float(conducted_core_comp) / float(total_core_comp) if total_core_comp > 0 else 0.0
        )

        # 2. Topic Coverage (Secondary Metric)
        # Total lesson plans (topics)
        stmt_total_topics = (
            select(func.count(LessonPlan.id))
            .where(
                LessonPlan.tenant_id == tenant_id,
                LessonPlan.course_id == course_id,
                LessonPlan.curriculum_id == curriculum_id,
                LessonPlan.is_current == True,
                LessonPlan.deleted_at.is_(None)
            )
        )
        total_topics_res = await self.db.execute(stmt_total_topics)
        total_topics = total_topics_res.scalar() or 0

        # Conducted lesson plans
        stmt_conducted_topics = (
            select(func.count(func.distinct(Session.lesson_plan_id)))
            .select_from(Session)
            .join(LessonPlan, Session.lesson_plan_id == LessonPlan.id)
            .where(
                Session.tenant_id == tenant_id,
                LessonPlan.course_id == course_id,
                LessonPlan.curriculum_id == curriculum_id,
                LessonPlan.deleted_at.is_(None)
            )
        )
        conducted_topics_res = await self.db.execute(stmt_conducted_topics)
        conducted_topics = conducted_topics_res.scalar() or 0

        topic_coverage = (
            float(conducted_topics) / float(total_topics) if total_topics > 0 else 0.0
        )

        # 3. Hours Coverage (Third Metric)
        # Total planned hours
        stmt_total_hours = (
            select(func.sum(LessonPlan.estimated_hours))
            .where(
                LessonPlan.tenant_id == tenant_id,
                LessonPlan.course_id == course_id,
                LessonPlan.curriculum_id == curriculum_id,
                LessonPlan.is_current == True,
                LessonPlan.deleted_at.is_(None)
            )
        )
        total_hours_res = await self.db.execute(stmt_total_hours)
        total_hours = float(total_hours_res.scalar() or 0.0)

        # Conducted hours
        stmt_conducted_hours = (
            select(func.sum(Session.actual_hours))
            .select_from(Session)
            .join(LessonPlan, Session.lesson_plan_id == LessonPlan.id)
            .where(
                Session.tenant_id == tenant_id,
                LessonPlan.course_id == course_id,
                LessonPlan.curriculum_id == curriculum_id,
                LessonPlan.deleted_at.is_(None)
            )
        )
        conducted_hours_res = await self.db.execute(stmt_conducted_hours)
        conducted_hours = float(conducted_hours_res.scalar() or 0.0)

        hours_coverage = (
            conducted_hours / total_hours if total_hours > 0.0 else 0.0
        )

        return {
            "competency_coverage": competency_coverage,
            "total_core_competencies": total_core_comp,
            "conducted_core_competencies": conducted_core_comp,
            "topic_coverage": topic_coverage,
            "total_topics": total_topics,
            "conducted_topics": conducted_topics,
            "hours_coverage": hours_coverage,
            "total_planned_hours": total_hours,
            "conducted_hours": conducted_hours,
        }
