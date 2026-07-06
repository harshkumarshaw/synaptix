"""DOAP Skills API endpoints."""

from typing import Annotated
from uuid import UUID

from app.schemas.doap import (
    DoapSessionCreate,
    DoapSessionResponse,
    DoapStateResponse,
)
from app.services.doap_service import DoapService, DoapServiceError
from fastapi import APIRouter, Depends, HTTPException, status

from packages.shared.auth.dependencies import require_roles
from packages.shared.auth.jwt import TokenPayload

router = APIRouter(prefix="/doap", tags=["doap"])


@router.post(
    "/records",
    response_model=DoapSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a DOAP session attempt and sign-off",
)
async def create_doap_record(
    data: DoapSessionCreate,
    current_user: Annotated[
        TokenPayload, Depends(require_roles(["faculty", "hod", "institution_admin", "admin"]))
    ],
    service: Annotated[DoapService, Depends(DoapService)],
) -> DoapSessionResponse:
    """
    Faculty records a student's DOAP session attempt.
    Auto-creates a digital logbook entry. Triggers remediation workflow on Re decision.
    """
    try:
        result = await service.submit_doap_session(
            tenant_id=current_user.tenant_uuid,
            user_id=current_user.user_id,
            data=data,
        )
        await service.db.commit()
        return result
    except DoapServiceError as e:
        await service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": e.code, "message": e.message},
        )


@router.get(
    "/student/{student_id}",
    response_model=list[DoapSessionResponse],
    summary="Get DOAP records for a student",
)
async def get_student_doap_records(
    student_id: UUID,
    current_user: Annotated[
        TokenPayload,
        Depends(require_roles(["student", "faculty", "hod", "institution_admin", "admin"])),
    ],
    service: Annotated[DoapService, Depends(DoapService)],
    competency_code: str | None = None,
) -> list[DoapSessionResponse]:
    """List all DOAP records for a student, optionally filtered by competency."""
    # Authorization check
    if "student" in current_user.roles and current_user.user_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other students' records",
        )

    return await service.get_doap_records(
        tenant_id=current_user.tenant_uuid,
        student_id=student_id,
        competency_code=competency_code,
    )


@router.get(
    "/student/{student_id}/competency/{competency_code}/state",
    response_model=DoapStateResponse,
    summary="Get current DOAP state for a competency",
)
async def get_doap_state(
    student_id: UUID,
    competency_code: str,
    current_user: Annotated[
        TokenPayload,
        Depends(require_roles(["student", "faculty", "hod", "institution_admin", "admin"])),
    ],
    service: Annotated[DoapService, Depends(DoapService)],
) -> DoapStateResponse:
    """Compute current DOAP state for student + competency."""
    # Authorization check
    if "student" in current_user.roles and current_user.user_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other students' records",
        )

    return await service.compute_state(
        tenant_id=current_user.tenant_uuid,
        student_id=student_id,
        competency_code=competency_code,
    )
