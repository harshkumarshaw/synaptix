from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.batch import Batch
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.program import Program
from app.models.timetable_entry import TimetableEntry
from packages.shared.db.session import get_db
from packages.shared.logging import get_logger

logger = get_logger(__name__)


class AcademicService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def get_programs(self, tenant_id: uuid.UUID) -> list[Program]:
        stmt = select(Program).where(Program.tenant_id == tenant_id, Program.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_courses(self, tenant_id: uuid.UUID) -> list[Course]:
        stmt = select(Course).where(Course.tenant_id == tenant_id, Course.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_batches(self, tenant_id: uuid.UUID) -> list[Batch]:
        stmt = select(Batch).where(Batch.tenant_id == tenant_id, Batch.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_timetable(
        self, tenant_id: uuid.UUID, batch_id: uuid.UUID
    ) -> list[TimetableEntry]:
        # Perform joins to eagerly load slot, course, and faculty (with faculty user)
        # to avoid N+1 queries per ADR-002 / Commandment 8
        stmt = (
            select(TimetableEntry)
            .options(
                joinedload(TimetableEntry.slot),
                joinedload(TimetableEntry.course),
                joinedload(TimetableEntry.faculty).joinedload(Faculty.user),
            )
            .where(
                TimetableEntry.tenant_id == tenant_id,
                TimetableEntry.batch_id == batch_id,
                TimetableEntry.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
