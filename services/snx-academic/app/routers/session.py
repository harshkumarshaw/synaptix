from __future__ import annotations

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException

from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload
from packages.shared.errors import ResourceNotFoundError, ValidationError
from app.schemas.session import SessionCreate, SessionResponse
from app.services.session_tracking_service import SessionTrackingService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a conducted academic session",
)
async def conduct_session(
    session_in: SessionCreate,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[SessionTrackingService, Depends(SessionTrackingService)],
) -> SessionResponse:
    try:
        session = await service.conduct_session(
            tenant_id=current_user.tenant_uuid,
            session_in=session_in,
            actor_id=current_user.user_uuid
        )
        # Fetch detailed session with relations
        return await service.get_session(current_user.tenant_uuid, session.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a session by ID",
)
async def get_session(
    session_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[SessionTrackingService, Depends(SessionTrackingService)],
) -> SessionResponse:
    try:
        session = await service.get_session(current_user.tenant_uuid, session_id)
        return session
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get(
    "/coverage/{course_id}/{curriculum_id}",
    status_code=status.HTTP_200_OK,
    summary="Calculate syllabus coverage metrics (triple-metric design)",
)
async def calculate_syllabus_coverage(
    course_id: uuid.UUID,
    curriculum_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[SessionTrackingService, Depends(SessionTrackingService)],
) -> dict:
    try:
        return await service.calculate_syllabus_coverage(
            tenant_id=current_user.tenant_uuid,
            course_id=course_id,
            curriculum_id=curriculum_id
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
