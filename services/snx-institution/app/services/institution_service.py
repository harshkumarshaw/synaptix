from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.db.session import get_db
from packages.shared.errors import StudentNotFoundError
from packages.shared.logging import get_logger
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.student import Student

logger = get_logger(__name__)


class InstitutionService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def get_departments(self, tenant_id: uuid.UUID) -> list[Department]:
        stmt = select(Department).where(
            Department.tenant_id == tenant_id,
            Department.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_faculty(self, tenant_id: uuid.UUID) -> list[Faculty]:
        stmt = (
            select(Faculty)
            .options(joinedload(Faculty.user))
            .where(
                Faculty.tenant_id == tenant_id,
                Faculty.deleted_at.is_(None)
            )
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_students(self, tenant_id: uuid.UUID) -> list[Student]:
        stmt = (
            select(Student)
            .options(joinedload(Student.user))
            .where(
                Student.tenant_id == tenant_id,
                Student.deleted_at.is_(None)
            )
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_student_status(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID, status: str
    ) -> Student:
        stmt = (
            select(Student)
            .options(joinedload(Student.user))
            .where(
                Student.tenant_id == tenant_id,
                Student.id == student_id,
                Student.deleted_at.is_(None)
            )
        )
        res = await self.db.execute(stmt)
        student = res.scalars().first()

        if not student:
            raise StudentNotFoundError(
                f"Student with ID {student_id} not found under this tenant.",
                details={"student_id": str(student_id)}
            )

        student.status = status
        await self.db.commit()

        logger.info(
            "Student status updated",
            extra={
                "student_id": str(student_id),
                "tenant_id": str(tenant_id),
                "new_status": status,
            }
        )
        return student
