from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdmissionApplication, Program
from app.schemas import AdmissionApplicationCreate, AdmissionApplicationResponse
from app.services.audit_logger import write_audit_log
from packages.shared.db.session import get_db
from packages.shared.errors import SynaptixError


class AdmissionServiceError(SynaptixError):
    """Exception raised for errors in the AdmissionService."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        self.code = f"SNX-ADM-{code}"
        super().__init__(message, details)


class AdmissionService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def create_application(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID, data: AdmissionApplicationCreate
    ) -> AdmissionApplicationResponse:
        """Create a new admission application."""
        # 1. Verify program exists
        prog_stmt = select(Program).where(
            Program.tenant_id == tenant_id,
            Program.id == data.applied_for_program_id,
        )
        prog_res = await self.db.execute(prog_stmt)
        program = prog_res.scalar_one_or_none()
        if not program:
            raise AdmissionServiceError("002", f"Program {data.applied_for_program_id} not found")

        # 2. Check unique application number (ADM-004)
        exist_stmt = select(AdmissionApplication).where(
            AdmissionApplication.tenant_id == tenant_id,
            AdmissionApplication.application_number == data.application_number,
            AdmissionApplication.deleted_at.is_(None),
        )
        exist_res = await self.db.execute(exist_stmt)
        if exist_res.scalar_one_or_none():
            raise AdmissionServiceError(
                "004", f"Application number {data.application_number} already exists"
            )

        # 3. Create record
        application = AdmissionApplication(
            tenant_id=tenant_id,
            application_number=data.application_number,
            student_name=data.student_name,
            applied_for_program_id=data.applied_for_program_id,
        )
        self.db.add(application)

        try:
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            raise AdmissionServiceError(
                "004", f"Application number {data.application_number} already exists"
            ) from e

        # 4. Write audit log
        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=user_id,
            action="CREATE_ADMISSION_APPLICATION",
            resource_type="admission_application",
            resource_id=application.id,
            new_values={
                "application_number": application.application_number,
                "student_name": application.student_name,
                "applied_for_program_id": str(application.applied_for_program_id),
            },
        )

        return AdmissionApplicationResponse.model_validate(application)

    async def get_application(
        self, tenant_id: uuid.UUID, application_id: uuid.UUID
    ) -> AdmissionApplicationResponse:
        """Fetch a single admission application by ID."""
        stmt = select(AdmissionApplication).where(
            AdmissionApplication.tenant_id == tenant_id,
            AdmissionApplication.id == application_id,
            AdmissionApplication.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        application = res.scalar_one_or_none()
        if not application:
            raise AdmissionServiceError("003", f"Admission application {application_id} not found")

        return AdmissionApplicationResponse.model_validate(application)

    async def list_applications(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 100
    ) -> list[AdmissionApplicationResponse]:
        """Fetch a paginated list of admission applications."""
        stmt = (
            select(AdmissionApplication)
            .where(
                AdmissionApplication.tenant_id == tenant_id,
                AdmissionApplication.deleted_at.is_(None),
            )
            .offset(offset)
            .limit(limit)
            .order_by(AdmissionApplication.created_at.desc())
        )
        res = await self.db.execute(stmt)
        applications = res.scalars().all()
        return [AdmissionApplicationResponse.model_validate(app) for app in applications]
