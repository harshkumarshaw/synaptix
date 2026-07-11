from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.exam import (
    EligibilityOverrideRequest,
    ExamEligibilityResponse,
    ExaminationCreate,
    ExaminationResponse,
    ExamResultResponse,
    ExamResultSubmit,
    ExamScheduleCreate,
    ExamScheduleResponse,
    IAAggregationRequest,
    IAAggregationResponse,
    MarkSheetResponse,
    ModerationRequest,
    ModerationResponse,
    PublishResultsResponse,
)
from app.services.exam_service import ExamService, ExamServiceError
from packages.shared.auth.dependencies import get_current_user, require_roles
from packages.shared.auth.jwt import TokenPayload
from packages.shared.db.session import get_db

router = APIRouter(prefix="/exams", tags=["exams"])


def _get_exam_service(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ExamService:
    return ExamService(db=db)


@router.post(
    "",
    response_model=ExaminationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["admin", "controller_of_examinations"]))],
)
async def create_examination(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    data: ExaminationCreate,
    service: ExamService = Depends(_get_exam_service),
) -> ExaminationResponse:
    try:
        exam = await service.create_examination(
            tenant_id=current_user.tenant_uuid,
            curriculum_id=data.curriculum_id,
            course_id=data.course_id,
            exam_type=data.exam_type,
            exam_session=data.exam_session,
            academic_year=data.academic_year,
            exam_date=data.exam_date,
            theory_max_marks=data.theory_max_marks,
            practical_max_marks=data.practical_max_marks,
            theory_pass_marks=data.theory_pass_marks,
            practical_pass_marks=data.practical_pass_marks,
            grace_marks_allowed=data.grace_marks_allowed,
            actor_user_id=current_user.user_uuid,
        )
        return exam
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/{id}/schedule",
    response_model=ExamScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["admin", "controller_of_examinations"]))],
)
async def create_exam_schedule(
    id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    data: ExamScheduleCreate,
    service: ExamService = Depends(_get_exam_service),
) -> ExamScheduleResponse:
    try:
        schedule = await service.create_exam_schedule(
            tenant_id=current_user.tenant_uuid,
            examination_id=id,
            room_id=data.room_id,
            start_time=data.start_time,
            end_time=data.end_time,
            invigilator_id=data.invigilator_id,
            actor_user_id=current_user.user_uuid,
        )
        return schedule
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/aggregate-ia",
    response_model=IAAggregationResponse,
    dependencies=[Depends(require_roles(["admin", "faculty", "controller_of_examinations"]))],
)
async def aggregate_ia(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    data: IAAggregationRequest,
    service: ExamService = Depends(_get_exam_service),
) -> IAAggregationResponse:
    try:
        agg = await service.aggregate_ia(
            tenant_id=current_user.tenant_uuid,
            student_id=data.student_id,
            course_id=data.course_id,
            professional_phase=data.professional_phase,
            actor_user_id=current_user.user_uuid,
        )
        return agg
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get(
    "/{id}/eligibility/{student_id}",
    response_model=ExamEligibilityResponse,
)
async def check_eligibility(
    id: uuid.UUID,
    student_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: ExamService = Depends(_get_exam_service),
) -> ExamEligibilityResponse:
    try:
        elig = await service.check_student_eligibility(
            tenant_id=current_user.tenant_uuid,
            student_id=student_id,
            examination_id=id,
            actor_user_id=current_user.user_uuid,
        )
        return elig
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/{id}/eligibility/override",
    response_model=ExamEligibilityResponse,
    dependencies=[Depends(require_roles(["principal", "dean"]))],
)
async def override_eligibility(
    id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    data: EligibilityOverrideRequest,
    service: ExamService = Depends(_get_exam_service),
) -> ExamEligibilityResponse:
    try:
        role = "dean" if "dean" in current_user.roles else "principal"
        elig = await service.override_eligibility(
            tenant_id=current_user.tenant_uuid,
            student_id=data.student_id,
            examination_id=id,
            role=role,
            reason=data.reason,
            actor_user_id=current_user.user_uuid,
        )
        return elig
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


# ---------------------------------------------------------------------------
# R4.3 — Result Processing Endpoints (ADR-040, 041, 045)
# ---------------------------------------------------------------------------


@router.post(
    "/results",
    response_model=ExamResultResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["faculty", "controller_of_examinations", "admin"]))],
)
async def submit_result(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    data: ExamResultSubmit,
    service: ExamService = Depends(_get_exam_service),
) -> ExamResultResponse:
    """Examiner submits marks for a student's examination (ADR-040)."""
    try:
        result = await service.submit_result(
            tenant_id=current_user.tenant_uuid,
            student_id=data.student_id,
            examination_id=data.examination_id,
            theory_marks=data.theory_marks,
            practical_marks=data.practical_marks,
            actor_user_id=current_user.user_uuid,
        )
        return result
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/moderation",
    response_model=ModerationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["faculty", "controller_of_examinations", "admin"]))],
)
async def record_moderation(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    data: ModerationRequest,
    service: ExamService = Depends(_get_exam_service),
) -> ModerationResponse:
    """Record multi-examiner moderation scores (ADR-048)."""
    try:
        mod = await service.record_moderation(
            tenant_id=current_user.tenant_uuid,
            exam_result_id=data.exam_result_id,
            examiner_1_marks=data.examiner_1_marks,
            examiner_2_marks=data.examiner_2_marks,
            max_marks=data.max_marks,
            examiner_3_marks=data.examiner_3_marks,
            actor_user_id=current_user.user_uuid,
        )
        return mod
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/results/{result_id}/verify",
    response_model=ExamResultResponse,
    dependencies=[Depends(require_roles(["hod", "admin"]))],
)
async def verify_result(
    result_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: ExamService = Depends(_get_exam_service),
) -> ExamResultResponse:
    """HOD verifies a draft result (draft → verified, ADR-045)."""
    try:
        result = await service.verify_result(
            tenant_id=current_user.tenant_uuid,
            exam_result_id=result_id,
            actor_user_id=current_user.user_uuid,
        )
        return result
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/results/{result_id}/approve",
    response_model=ExamResultResponse,
    dependencies=[Depends(require_roles(["principal", "admin"]))],
)
async def approve_result(
    result_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: ExamService = Depends(_get_exam_service),
) -> ExamResultResponse:
    """Principal approves a verified result (verified → approved, ADR-045)."""
    try:
        result = await service.approve_result(
            tenant_id=current_user.tenant_uuid,
            exam_result_id=result_id,
            actor_user_id=current_user.user_uuid,
        )
        return result
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/{examination_id}/publish",
    response_model=PublishResultsResponse,
    dependencies=[Depends(require_roles(["principal", "controller_of_examinations", "admin"]))],
)
async def publish_results(
    examination_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: ExamService = Depends(_get_exam_service),
) -> PublishResultsResponse:
    """Publish all approved results for an examination (ADR-045)."""
    try:
        count = await service.publish_results(
            tenant_id=current_user.tenant_uuid,
            examination_id=examination_id,
            actor_user_id=current_user.user_uuid,
        )
        return PublishResultsResponse(
            published_count=count,
            message=f"{count} result(s) published successfully.",
        )
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


# ---------------------------------------------------------------------------
# R4.4 — Mark Sheet Generation (ADR-042)
# ---------------------------------------------------------------------------


@router.get(
    "/mark-sheet/{student_id}/{academic_year}",
    response_model=MarkSheetResponse,
)
async def get_mark_sheet(
    student_id: uuid.UUID,
    academic_year: str,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: ExamService = Depends(_get_exam_service),
) -> MarkSheetResponse:
    """Generate or retrieve a mark sheet PDF for a student for a given academic year (ADR-042)."""
    try:
        mark_sheet = await service.generate_mark_sheet(
            tenant_id=current_user.tenant_uuid,
            student_id=student_id,
            academic_year=academic_year,
            actor_user_id=current_user.user_uuid,
        )
        return mark_sheet
    except ExamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
