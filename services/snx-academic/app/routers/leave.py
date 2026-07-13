"""
Leave Management Router — Phase 2 (A-12).

Endpoints:
  POST   /leave/requests               — Student: create leave request
  GET    /leave/requests               — List leave requests (filtered)
  POST   /leave/requests/{id}/approve  — HOD/Principal: approve
  POST   /leave/requests/{id}/reject   — HOD/Principal: reject
  POST   /leave/requests/{id}/cancel   — Student/Admin: cancel approved leave
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stubs import Student
from app.schemas.leave import (
    LeaveApproveRequest,
    LeaveRejectRequest,
    LeaveRequestCreate,
    LeaveRequestOut,
)
from app.services.leave_service import LeaveService
from packages.shared.auth.dependencies import get_current_user, require_roles
from packages.shared.auth.jwt import TokenPayload
from packages.shared.db.session import get_db
from packages.shared.errors import InvalidStateTransitionError, ResourceNotFoundError

router = APIRouter(prefix="/leave", tags=["leave"])


def _get_leave_service(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> LeaveService:
    """FastAPI dependency: construct LeaveService."""
    return LeaveService(
        db=db,
        tenant_id=current_user.tenant_uuid,
        actor_id=current_user.user_uuid,  # type: ignore[attr-defined]
    )


@router.post(
    "/requests",
    response_model=LeaveRequestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a leave request",
)
async def create_leave_request(
    req: LeaveRequestCreate,
    current_user: Annotated[TokenPayload, Depends(require_roles(["student"]))],
    service: Annotated[LeaveService, Depends(_get_leave_service)],
) -> LeaveRequestOut:
    """Student creates a leave request. Starts in pending state."""
    try:
        student_uuid = current_user.user_uuid  # type: ignore[attr-defined]
        stmt = select(Student.id).where(
            (Student.user_id == current_user.user_uuid) | (Student.id == current_user.user_uuid)  # type: ignore[attr-defined]
        )
        resolved_id = (await service._db.execute(stmt)).scalar_one_or_none()
        if resolved_id:
            student_uuid = resolved_id

        leave = await service.create_leave_request(
            student_id=student_uuid,
            req=req,
        )
        return LeaveRequestOut.model_validate(leave)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/requests",
    response_model=list[LeaveRequestOut],
    status_code=status.HTTP_200_OK,
    summary="List leave requests",
)
async def list_leave_requests(
    student_id: uuid.UUID | None = None,
    leave_status: str | None = None,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,  # type: ignore[assignment]
    service: Annotated[LeaveService, Depends(_get_leave_service)] = None,  # type: ignore[assignment]
) -> list[LeaveRequestOut]:
    """List leave requests. Student sees own; HOD/Admin sees all or filtered."""
    resolved_student_id = student_id
    if not resolved_student_id and current_user and "student" in current_user.roles:
        resolved_student_id = current_user.user_uuid  # type: ignore[attr-defined]

    if resolved_student_id:
        stmt = select(Student.id).where(
            (Student.user_id == resolved_student_id) | (Student.id == resolved_student_id)
        )
        db_id = (await service._db.execute(stmt)).scalar_one_or_none()
        if db_id:
            resolved_student_id = db_id

    requests = await service.get_leave_requests(student_id=resolved_student_id, status=leave_status)
    return [LeaveRequestOut.model_validate(r) for r in requests]


@router.post(
    "/requests/{leave_request_id}/approve",
    response_model=LeaveRequestOut,
    status_code=status.HTTP_200_OK,
    summary="Approve a leave request (HOD / Principal)",
)
async def approve_leave(
    leave_request_id: uuid.UUID,
    req: LeaveApproveRequest,
    current_user: Annotated[
        TokenPayload, Depends(require_roles(["hod", "principal", "institution_admin"]))
    ],
    service: Annotated[LeaveService, Depends(_get_leave_service)],
) -> LeaveRequestOut:
    """Approve a pending leave request. Auto-marks attendance for events in window."""
    try:
        leave = await service.approve_leave(leave_request_id, req.remarks)
        return LeaveRequestOut.model_validate(leave)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.post(
    "/requests/{leave_request_id}/reject",
    response_model=LeaveRequestOut,
    status_code=status.HTTP_200_OK,
    summary="Reject a leave request (HOD / Principal)",
)
async def reject_leave(
    leave_request_id: uuid.UUID,
    req: LeaveRejectRequest,
    current_user: Annotated[
        TokenPayload, Depends(require_roles(["hod", "principal", "institution_admin"]))
    ],
    service: Annotated[LeaveService, Depends(_get_leave_service)],
) -> LeaveRequestOut:
    """Reject a pending leave request with mandatory remarks."""
    try:
        leave = await service.reject_leave(leave_request_id, req.remarks)
        return LeaveRequestOut.model_validate(leave)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.post(
    "/requests/{leave_request_id}/cancel",
    response_model=LeaveRequestOut,
    status_code=status.HTTP_200_OK,
    summary="Cancel an approved leave request",
)
async def cancel_leave(
    leave_request_id: uuid.UUID,
    current_user: Annotated[
        TokenPayload, Depends(require_roles(["student", "hod", "institution_admin"]))
    ],
    service: Annotated[LeaveService, Depends(_get_leave_service)],
) -> LeaveRequestOut:
    """Cancel an approved leave. Rolls back auto-generated attendance rows."""
    try:
        leave = await service.cancel_leave(leave_request_id)
        return LeaveRequestOut.model_validate(leave)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
