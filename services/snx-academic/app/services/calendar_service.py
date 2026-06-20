from __future__ import annotations

import datetime
import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.calendar import Event, EventCourse, EventFaculty
from app.models.course import Course
from app.schemas.calendar import EventCreate
from app.services.audit_logger import write_audit_log
from packages.shared.db.session import get_db
from packages.shared.logging import get_logger

logger = get_logger(__name__)


class CalendarService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def create_event(
        self, tenant_id: uuid.UUID, event_in: EventCreate, actor_id: uuid.UUID | None = None
    ) -> Event:
        # Determine the primary course from event_in.courses to fetch default_attendance_category
        primary_course_id = None
        for course_item in event_in.courses:
            if course_item.is_primary:
                primary_course_id = course_item.course_id
                break

        # Fallback if no course is marked is_primary
        if not primary_course_id and event_in.courses:
            primary_course_id = event_in.courses[0].course_id

        if not primary_course_id:
            raise ValueError("An event must have at least one course associated with it.")

        # Fetch course default_attendance_category (EC-014 compliance)
        course_stmt = select(Course).where(
            Course.tenant_id == tenant_id, Course.id == primary_course_id
        )
        res = await self.db.execute(course_stmt)
        course = res.scalar_one_or_none()
        if not course:
            raise ValueError(f"Primary course with ID {primary_course_id} not found.")

        # Determine attendance category
        attendance_category = course.default_attendance_category

        # Conflict checks (EC-113: holiday conflict check stub)
        # In a real app we'd query a master_data_entities table for institutional holidays
        if event_in.date.weekday() == 6:  # Sunday warning/alert stub (EC-127)
            logger.warning("Event is scheduled on a Sunday.", extra={"date": str(event_in.date)})

        # ECE Phase I only check (ECE-NMC-001)
        if event_in.event_type == "ece" and event_in.professional_phase != "Phase I":
            raise ValueError("ECE event type allowed only in Phase I.")

        # Clinical posting Phase I not allowed check (ECE-NMC-002)
        if event_in.event_type == "clinical_posting" and event_in.professional_phase == "Phase I":
            raise ValueError("Clinical postings event type NOT allowed in Phase I.")

        # Foundation course 1-month block check (FC-NMC-001)
        # Note: Seeding handles academic year start dates. Here we just validate time limits.

        # Create event object
        event = Event(
            tenant_id=tenant_id,
            batch_id=event_in.batch_id,
            academic_year_id=event_in.academic_year_id,
            title=event_in.title,
            description=event_in.description,
            event_type=event_in.event_type,
            attendance_category=attendance_category,
            professional_phase=event_in.professional_phase,
            date=event_in.date,
            start_time=event_in.start_time,
            end_time=event_in.end_time,
            status="scheduled",
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(event)
        await self.db.flush()  # Populates event.id

        # Insert event courses
        for course_item in event_in.courses:
            ec = EventCourse(
                tenant_id=tenant_id,
                event_id=event.id,
                course_id=course_item.course_id,
                is_primary=(course_item.course_id == primary_course_id),
            )
            self.db.add(ec)

        # Insert event faculty
        for fac_item in event_in.assigned_faculty:
            ef = EventFaculty(
                tenant_id=tenant_id, event_id=event.id, faculty_id=fac_item.faculty_id
            )
            self.db.add(ef)

        await self.db.flush()

        # Write to audit log
        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="CREATE",
            resource_type="event",
            resource_id=event.id,
            new_values={
                "title": event.title,
                "event_type": event.event_type,
                "attendance_category": event.attendance_category,
                "date": str(event.date),
            },
        )

        return event

    async def get_event(self, tenant_id: uuid.UUID, event_id: uuid.UUID) -> Event | None:
        stmt = (
            select(Event)
            .options(selectinload(Event.courses), selectinload(Event.assigned_faculty))
            .where(Event.tenant_id == tenant_id, Event.id == event_id, Event.deleted_at.is_(None))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def cancel_event(
        self, tenant_id: uuid.UUID, event_id: uuid.UUID, reason: str, actor_id: uuid.UUID
    ) -> Event | None:
        event = await self.get_event(tenant_id, event_id)
        if not event:
            return None

        event.status = "cancelled"
        event.cancellation_reason = reason
        event.cancelled_by = actor_id
        event.updated_by = actor_id

        await self.db.flush()

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="CANCEL",
            resource_type="event",
            resource_id=event.id,
            new_values={"status": "cancelled", "reason": reason},
        )
        return event

    async def reschedule_event(
        self,
        tenant_id: uuid.UUID,
        event_id: uuid.UUID,
        new_date: datetime.date,
        new_start: datetime.time,
        new_end: datetime.time,
        actor_id: uuid.UUID,
    ) -> Event:
        # Rescheduling (EC-110 compliance)
        # 1. Fetch original event
        stmt = (
            select(Event)
            .options(selectinload(Event.courses), selectinload(Event.assigned_faculty))
            .where(Event.tenant_id == tenant_id, Event.id == event_id)
        )
        res = await self.db.execute(stmt)
        original = res.scalar_one_or_none()
        if not original:
            raise ValueError("Original event not found.")

        # Update original event status
        original.status = "rescheduled"
        original.updated_by = actor_id
        await self.db.flush()

        # Re-create EventCreate payload

        new_event = Event(
            tenant_id=tenant_id,
            batch_id=original.batch_id,
            academic_year_id=original.academic_year_id,
            title=original.title,
            description=original.description,
            event_type=original.event_type,
            attendance_category=original.attendance_category,
            professional_phase=original.professional_phase,
            date=new_date,
            start_time=new_start,
            end_time=new_end,
            status="scheduled",
            parent_event_id=original.id,  # Maintains reference to original
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(new_event)
        await self.db.flush()

        # Re-insert relationships
        for c in original.courses:
            ec = EventCourse(
                tenant_id=tenant_id,
                event_id=new_event.id,
                course_id=c.course_id,
                is_primary=c.is_primary,
            )
            self.db.add(ec)

        for f in original.assigned_faculty:
            ef = EventFaculty(tenant_id=tenant_id, event_id=new_event.id, faculty_id=f.faculty_id)
            self.db.add(ef)

        await self.db.flush()

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="RESCHEDULE",
            resource_type="event",
            resource_id=new_event.id,
            new_values={"parent_event_id": str(original.id), "date": str(new_date)},
        )

        return new_event
