from __future__ import annotations

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException

from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload
from app.schemas.curriculum_migration import CurriculumMigrationAuditCreate, CurriculumMigrationAuditResponse
from app.services.curriculum_migration_service import CurriculumMigrationService

router = APIRouter(prefix="/curriculum-migrations", tags=["curriculum-migrations"])


@router.post(
    "",
    response_model=CurriculumMigrationAuditResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a student curriculum migration audit event",
)
async def record_migration(
    migration_in: CurriculumMigrationAuditCreate,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[CurriculumMigrationService, Depends(CurriculumMigrationService)],
) -> CurriculumMigrationAuditResponse:
    try:
        audit = await service.record_migration(
            tenant_id=current_user.tenant_uuid,
            migration_in=migration_in,
            actor_id=current_user.user_uuid
        )
        return audit
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/student/{student_id}",
    response_model=list[CurriculumMigrationAuditResponse],
    status_code=status.HTTP_200_OK,
    summary="Get curriculum migration history for a student",
)
async def get_migration_history(
    student_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[CurriculumMigrationService, Depends(CurriculumMigrationService)],
) -> list[CurriculumMigrationAuditResponse]:
    history = await service.get_migration_history(
        tenant_id=current_user.tenant_uuid,
        student_id=student_id
    )
    return history
