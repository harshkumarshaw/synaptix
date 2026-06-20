from __future__ import annotations

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException

from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload
from packages.shared.errors import ResourceNotFoundError, ValidationError, DuplicateRecordError
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanUpdate, LessonPlanResponse
from app.services.lesson_plan_service import LessonPlanService

router = APIRouter(prefix="/lesson-plans", tags=["lesson-plans"])


@router.post(
    "",
    response_model=LessonPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lesson plan template",
)
async def create_lesson_plan(
    lp_in: LessonPlanCreate,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LessonPlanService, Depends(LessonPlanService)],
) -> LessonPlanResponse:
    try:
        lp = await service.create_lesson_plan(
            tenant_id=current_user.tenant_uuid,
            lp_in=lp_in,
            actor_id=current_user.user_uuid
        )
        return lp
    except DuplicateRecordError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get(
    "/{lp_id}",
    response_model=LessonPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a lesson plan by ID",
)
async def get_lesson_plan(
    lp_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LessonPlanService, Depends(LessonPlanService)],
) -> LessonPlanResponse:
    try:
        lp = await service.get_lesson_plan(current_user.tenant_uuid, lp_id)
        return lp
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.put(
    "/{lp_id}",
    response_model=LessonPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a lesson plan (spawns new version if not in draft)",
)
async def update_lesson_plan(
    lp_id: uuid.UUID,
    lp_in: LessonPlanUpdate,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LessonPlanService, Depends(LessonPlanService)],
) -> LessonPlanResponse:
    try:
        lp = await service.update_lesson_plan(
            tenant_id=current_user.tenant_uuid,
            lp_id=lp_id,
            lp_in=lp_in,
            actor_id=current_user.user_uuid
        )
        return lp
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except DuplicateRecordError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/{lp_id}/submit",
    response_model=LessonPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a lesson plan for approval (initiates HOD approval workflow)",
)
async def submit_for_approval(
    lp_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[LessonPlanService, Depends(LessonPlanService)],
) -> LessonPlanResponse:
    try:
        lp = await service.submit_for_approval(
            tenant_id=current_user.tenant_uuid,
            lp_id=lp_id,
            actor_id=current_user.user_uuid
        )
        return lp
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
