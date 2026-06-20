from __future__ import annotations

import uuid
from typing import Annotated

from app.schemas.logbook import (
    AetcomRecordResponse,
    AetcomReflectionSubmit,
    AetcomSignoffPayload,
    FoundationCourseHoursLog,
    FoundationCourseRecordResponse,
    FoundationCourseSignoffPayload,
)
from app.services.logbook_service import LogbookService
from fastapi import APIRouter, Depends, HTTPException, status

from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload
from packages.shared.errors import DuplicateRecordError, ValidationError

router = APIRouter(prefix="/logbook", tags=["logbook"])


# ============================================================================
# Foundation Course Endpoints
# ============================================================================


@router.post(
    "/foundation/hours",
    response_model=FoundationCourseRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Log hours completed for a foundation course module",
)
async def log_foundation_hours(
    log_in: FoundationCourseHoursLog,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
) -> FoundationCourseRecordResponse:
    try:
        record = await service.log_foundation_hours(
            tenant_id=current_user.tenant_uuid, log_in=log_in, actor_id=current_user.user_uuid
        )
        return record
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/foundation/signoff",
    response_model=FoundationCourseRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Faculty sign-off for a foundation course module",
)
async def signoff_foundation_module(
    payload: FoundationCourseSignoffPayload,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
) -> FoundationCourseRecordResponse:
    try:
        record = await service.signoff_foundation_module(
            tenant_id=current_user.tenant_uuid,
            payload=payload,
            signed_off_by=current_user.user_uuid,
        )
        return record
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get(
    "/foundation/student/{student_id}",
    response_model=list[FoundationCourseRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Get foundation course progress and completion status for a student",
)
async def get_student_foundation_progress(
    student_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
) -> list[FoundationCourseRecordResponse]:
    records = await service.get_student_foundation_progress(
        tenant_id=current_user.tenant_uuid, student_id=student_id
    )
    return records


# ============================================================================
# AETCOM Endpoints
# ============================================================================


@router.post(
    "/aetcom/reflection",
    response_model=AetcomRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit student reflection for an AETCOM module/competency",
)
async def submit_reflection(
    submit_in: AetcomReflectionSubmit,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
) -> AetcomRecordResponse:
    try:
        record = await service.submit_reflection(
            tenant_id=current_user.tenant_uuid,
            student_id=current_user.user_uuid,  # Assuming student logged in is the actor
            submit_in=submit_in,
            actor_id=current_user.user_uuid,
        )
        return record
    except DuplicateRecordError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/aetcom/signoff",
    response_model=AetcomRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Faculty sign-off and assessment for an AETCOM module/competency",
)
async def signoff_aetcom_competency(
    payload: AetcomSignoffPayload,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
) -> AetcomRecordResponse:
    try:
        record = await service.signoff_aetcom_competency(
            tenant_id=current_user.tenant_uuid,
            payload=payload,
            signed_off_by=current_user.user_uuid,
        )
        return record
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get(
    "/aetcom/student/{student_id}",
    response_model=list[AetcomRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Get AETCOM reflection and completion records for a student",
)
async def get_student_aetcom_records(
    student_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
    phase: str | None = None,
) -> list[AetcomRecordResponse]:
    records = await service.get_student_aetcom_records(
        tenant_id=current_user.tenant_uuid, student_id=student_id, phase=phase
    )
    return records
