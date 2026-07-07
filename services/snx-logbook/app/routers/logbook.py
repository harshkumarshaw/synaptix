from __future__ import annotations

import uuid
from typing import Annotated

from app.schemas import (
    AetcomRecordResponse,
    AetcomReflectionSubmit,
    AetcomSignoffPayload,
    FoundationCourseHoursLog,
    FoundationCourseRecordResponse,
    FoundationCourseSignoffPayload,
    LogbookAssessmentResponse,
    LogbookEntryCreate,
    LogbookEntryResponse,
    LogbookEntrySubmitRequest,
    LogbookSignoffRequest,
)
from app.services.logbook_service import LogbookService, LogbookServiceError
from fastapi import APIRouter, Depends, HTTPException, Query, status

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


# ============================================================================
# Logbook Phase 2 Endpoints
# ============================================================================


@router.post(
    "/entries",
    response_model=LogbookEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Student creates a new logbook entry",
)
async def create_logbook_entry(
    data: LogbookEntryCreate,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
) -> LogbookEntryResponse:
    try:
        result = await service.create_entry(
            tenant_id=current_user.tenant_uuid,
            user_id=current_user.user_uuid,
            data=data,
        )
        return result
    except LogbookServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": e.code, "message": e.message},
        )


@router.patch(
    "/entries/{entry_id}/submit",
    response_model=LogbookEntryResponse,
    summary="Student submits entry for faculty review",
)
async def submit_logbook_entry(
    entry_id: uuid.UUID,
    data: LogbookEntrySubmitRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
) -> LogbookEntryResponse:
    try:
        result = await service.submit_entry(
            tenant_id=current_user.tenant_uuid,
            student_id=current_user.user_uuid,
            entry_id=entry_id,
            data=data,
        )
        return result
    except LogbookServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": e.code, "message": e.message},
        )


@router.patch(
    "/entries/{entry_id}/signoff",
    response_model=LogbookEntryResponse,
    summary="Faculty signs off on a submitted logbook entry",
)
async def signoff_logbook_entry(
    entry_id: uuid.UUID,
    data: LogbookSignoffRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
) -> LogbookEntryResponse:
    try:
        result = await service.signoff_entry(
            tenant_id=current_user.tenant_uuid,
            faculty_id=current_user.user_uuid,
            entry_id=entry_id,
            data=data,
        )
        return result
    except LogbookServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": e.code, "message": e.message},
        )


@router.get(
    "/entries",
    response_model=list[LogbookEntryResponse],
    summary="List logbook entries for a student with optional filters",
)
async def list_logbook_entries(
    student_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
    subject_code: str | None = None,
    professional_phase: str | None = None,
    entry_status: str | None = Query(None, alias="status"),
    competency_code: str | None = None,
    is_core: bool | None = None,
) -> list[LogbookEntryResponse]:
    # Authorization check: student can only list their own entries
    # Admin / Faculty / HOD can list any
    # Note: current_user.role or similar holds the role name. We can inspect payload.
    if current_user.role == "student" and current_user.user_uuid != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await service.get_student_entries(
        tenant_id=current_user.tenant_uuid,
        student_id=student_id,
        subject_code=subject_code,
        professional_phase=professional_phase,
        status=entry_status,
        competency_code=competency_code,
        is_core=is_core,
    )
    return [LogbookEntryResponse.model_validate(r) for r in result]


@router.get(
    "/assessments/{student_id}/{subject_code}/{professional_phase}",
    response_model=LogbookAssessmentResponse,
    summary="Get IA marks assessment for a student's subject/phase",
)
async def get_ia_assessment(
    student_id: uuid.UUID,
    subject_code: str,
    professional_phase: str,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LogbookService, Depends(LogbookService)],
) -> LogbookAssessmentResponse:
    if current_user.role == "student" and current_user.user_uuid != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await service.get_ia_assessment(
        tenant_id=current_user.tenant_uuid,
        student_id=student_id,
        subject_code=subject_code,
        professional_phase=professional_phase,
    )
    return LogbookAssessmentResponse.model_validate(result)
