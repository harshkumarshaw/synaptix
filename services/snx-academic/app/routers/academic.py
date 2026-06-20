from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.academic import (
    BatchResponse,
    CourseResponse,
    ProgramResponse,
    TimetableEntryResponse,
    TimetableSlotResponse,
)
from app.services.academic_service import AcademicService
from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload

router = APIRouter(prefix="/academic", tags=["academic"])


@router.get(
    "/programs",
    response_model=list[ProgramResponse],
    status_code=status.HTTP_200_OK,
    summary="List all programs for the tenant",
)
async def list_programs(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AcademicService, Depends(AcademicService)],
) -> list[ProgramResponse]:
    programs = await service.get_programs(current_user.tenant_uuid)
    return [ProgramResponse.from_orm(p) for p in programs]


@router.get(
    "/courses",
    response_model=list[CourseResponse],
    status_code=status.HTTP_200_OK,
    summary="List all courses for the tenant",
)
async def list_courses(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AcademicService, Depends(AcademicService)],
) -> list[CourseResponse]:
    courses = await service.get_courses(current_user.tenant_uuid)
    return [CourseResponse.from_orm(c) for c in courses]


@router.get(
    "/batches",
    response_model=list[BatchResponse],
    status_code=status.HTTP_200_OK,
    summary="List all batches for the tenant",
)
async def list_batches(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AcademicService, Depends(AcademicService)],
) -> list[BatchResponse]:
    batches = await service.get_batches(current_user.tenant_uuid)
    return [BatchResponse.from_orm(b) for b in batches]


@router.get(
    "/timetable/{batch_id}",
    response_model=list[TimetableEntryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get timetable for a batch",
)
async def get_timetable(
    batch_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AcademicService, Depends(AcademicService)],
) -> list[TimetableEntryResponse]:
    entries = await service.get_timetable(current_user.tenant_uuid, batch_id)
    return [
        TimetableEntryResponse(
            id=e.id,
            batch_id=e.batch_id,
            course_id=e.course_id,
            course_code=e.course.code,
            course_name=e.course.name,
            faculty_id=e.faculty_id,
            faculty_name=e.faculty.user.full_name,
            slot=TimetableSlotResponse.from_orm(e.slot),
            room_number=e.room_number,
        )
        for e in entries
    ]
