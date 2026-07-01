from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas import AdmissionApplicationCreate, AdmissionApplicationResponse
from app.services.admission_service import AdmissionService, AdmissionServiceError
from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload

router = APIRouter(prefix="/admissions", tags=["admissions"])


@router.post(
    "/applications",
    response_model=AdmissionApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new admission application",
)
async def create_admission_application(
    data: AdmissionApplicationCreate,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AdmissionService, Depends(AdmissionService)],
) -> AdmissionApplicationResponse:
    try:
        # Authorization check: only admin role allowed
        if "admin" not in current_user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        result = await service.create_application(
            tenant_id=current_user.tenant_uuid,
            user_id=current_user.user_id,
            data=data,
        )
        return result
    except AdmissionServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": e.code, "message": e.message},
        )


@router.get(
    "/applications",
    response_model=list[AdmissionApplicationResponse],
    summary="List all admission applications (paginated)",
)
async def list_admission_applications(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AdmissionService, Depends(AdmissionService)],
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> list[AdmissionApplicationResponse]:
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await service.list_applications(
        tenant_id=current_user.tenant_uuid,
        offset=offset,
        limit=limit,
    )
    return result


@router.get(
    "/applications/{application_id}",
    response_model=AdmissionApplicationResponse,
    summary="Get details of an admission application by ID",
)
async def get_admission_application(
    application_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AdmissionService, Depends(AdmissionService)],
) -> AdmissionApplicationResponse:
    try:
        if "admin" not in current_user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        result = await service.get_application(
            tenant_id=current_user.tenant_uuid,
            application_id=application_id,
        )
        return result
    except AdmissionServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": e.code, "message": e.message},
        )
