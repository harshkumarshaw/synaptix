"""
Electives API router — Phase 2 (A-08).

Endpoints:
  POST   /electives/                          — create elective (institution_admin)
  POST   /electives/preferences               — submit student preferences
  GET    /electives/preferences/{student_id}  — get student's preferences
  POST   /electives/allocate                  — run allocation (institution_admin)
  GET    /electives/allocations/{student_id}  — get student's confirmed allocations
  DELETE /electives/allocations/{allocation_id} — withdraw allocation

Audit log writes documented in ElectiveService docstring.
All endpoints require @require_tenant_context (enforced via TenantContextMiddleware).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from app.schemas.electives import (
    AllocationResponse,
    AllocationRunRequest,
    AllocationRunResponse,
    ElectiveCreate,
    ElectiveResponse,
    PreferenceResponse,
    PreferencesSubmitRequest,
)
from app.services.elective_service import (
    ElectiveBlockAllocatedError,
    ElectiveLockError,
    ElectiveService,
    ElectiveWrongBlockError,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status

from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload
from packages.shared.errors import ResourceNotFoundError, ValidationError

router = APIRouter(prefix="/electives", tags=["electives"])


# ---------------------------------------------------------------------------
# POST /electives/ — create elective
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=ElectiveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new elective offering for a curriculum block",
)
async def create_elective(
    payload: ElectiveCreate,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[ElectiveService, Depends(ElectiveService)],
) -> ElectiveResponse:
    """
    Create a new elective. Restricted to institution_admin and academic_office_head roles.

    NMC CBME 2019 Reg 7: block_duration_weeks must be 2 (default).
    """
    try:
        return await service.create_elective(
            tenant_id=current_user.tenant_uuid,
            payload=payload,
            actor_id=current_user.user_uuid,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


# ---------------------------------------------------------------------------
# POST /electives/preferences — submit/replace student preferences
# ---------------------------------------------------------------------------


@router.post(
    "/preferences",
    response_model=list[PreferenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit or replace student's ranked elective preferences for a block",
)
async def submit_preferences(
    payload: PreferencesSubmitRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[ElectiveService, Depends(ElectiveService)],
) -> list[PreferenceResponse]:
    """
    Full-block replace: submitting preferences REPLACES all existing preferences
    for the specified student+block in a single transaction.

    Returns 409 if the block is already allocated (SNX-ELEC-002).
    Returns 422 if rank positions are invalid or elective belongs to wrong block.
    """
    try:
        return await service.submit_preferences(
            tenant_id=current_user.tenant_uuid,
            payload=payload,
            actor_id=current_user.user_uuid,
        )
    except ElectiveBlockAllocatedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except ElectiveWrongBlockError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


# ---------------------------------------------------------------------------
# GET /electives/preferences/{student_id} — get student preferences
# ---------------------------------------------------------------------------


@router.get(
    "/preferences/{student_id}",
    response_model=list[PreferenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a student's ranked elective preferences",
)
async def get_student_preferences(
    student_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[ElectiveService, Depends(ElectiveService)],
    block: str | None = Query(default=None, description="Filter by block: 'Block 1' or 'Block 2'"),
) -> list[PreferenceResponse]:
    return await service.get_student_preferences(
        tenant_id=current_user.tenant_uuid,
        student_id=student_id,
        block=block,
    )


# ---------------------------------------------------------------------------
# POST /electives/allocate — run allocation
# ---------------------------------------------------------------------------


@router.post(
    "/allocate",
    response_model=AllocationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run elective allocation algorithm for a curriculum block",
)
async def run_allocation(
    request: AllocationRunRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[ElectiveService, Depends(ElectiveService)],
) -> AllocationRunResponse:
    """
    Run FCFS or Ranked allocation.

    - dry_run=true: returns result without committing any writes. Fully idempotent.
    - force_reallocate='additive': allocates only unallocated students.
    - force_reallocate='full': clears existing allocations, re-runs from scratch.
      Requires explicit confirmation from caller (non-idempotent).

    Returns 409 if another allocation run holds the row lock (SNX-ELEC-004).
    Returns 404 if no electives found for the given curriculum + block.
    """
    try:
        return await service.run_allocation(
            tenant_id=current_user.tenant_uuid,
            request=request,
            actor_id=current_user.user_uuid,
        )
    except ElectiveLockError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": e.code, "message": e.message, "retry_after": 5},
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


# ---------------------------------------------------------------------------
# GET /electives/allocations/{student_id} — get student allocations
# ---------------------------------------------------------------------------


@router.get(
    "/allocations/{student_id}",
    response_model=list[AllocationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get confirmed elective allocations for a student",
)
async def get_student_allocations(
    student_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[ElectiveService, Depends(ElectiveService)],
    block: str | None = Query(default=None, description="Filter by block: 'Block 1' or 'Block 2'"),
) -> list[AllocationResponse]:
    return await service.get_student_allocations(
        tenant_id=current_user.tenant_uuid,
        student_id=student_id,
        block=block,
    )


# ---------------------------------------------------------------------------
# DELETE /electives/allocations/{allocation_id} — withdraw allocation
# ---------------------------------------------------------------------------


@router.delete(
    "/allocations/{allocation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Withdraw a student's elective allocation",
)
async def withdraw_allocation(
    allocation_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[ElectiveService, Depends(ElectiveService)],
) -> None:
    """
    Soft-deletes the allocation. Returns 404 if not found or already withdrawn.
    Audit log entry created: action=withdraw_allocation.
    """
    try:
        await service.withdraw_allocation(
            tenant_id=current_user.tenant_uuid,
            allocation_id=allocation_id,
            actor_id=current_user.user_uuid,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
