from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from packages.shared.auth.dependencies import get_current_user, require_roles
from packages.shared.auth.jwt import TokenPayload
from app.schemas.institution import (
    DepartmentResponse,
    FacultyResponse,
    StudentResponse,
    StudentStatusUpdateRequest,
)
from app.services.institution_service import InstitutionService

router = APIRouter(prefix="/institution", tags=["institution"])


@router.get(
    "/departments",
    response_model=list[DepartmentResponse],
    status_code=status.HTTP_200_OK,
    summary="List all departments for the tenant",
)
async def list_departments(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[InstitutionService, Depends(InstitutionService)],
) -> list[DepartmentResponse]:
    departments = await service.get_departments(current_user.tenant_uuid)
    return [DepartmentResponse.from_orm(d) for d in departments]


@router.get(
    "/faculty",
    response_model=list[FacultyResponse],
    status_code=status.HTTP_200_OK,
    summary="List all faculty profiles for the tenant",
)
async def list_faculty(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[InstitutionService, Depends(InstitutionService)],
) -> list[FacultyResponse]:
    faculty_list = await service.get_faculty(current_user.tenant_uuid)
    return [
        FacultyResponse(
            id=f.id,
            tenant_id=f.tenant_id,
            user_id=f.user_id,
            full_name=f.user.full_name,
            email=f.user.email,
            department_id=f.department_id,
            designation=f.designation,
            employee_id=f.employee_id,
            is_active=f.is_active,
        )
        for f in faculty_list
    ]


@router.get(
    "/students",
    response_model=list[StudentResponse],
    status_code=status.HTTP_200_OK,
    summary="List all student profiles for the tenant",
)
async def list_students(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[InstitutionService, Depends(InstitutionService)],
) -> list[StudentResponse]:
    students = await service.get_students(current_user.tenant_uuid)
    return [
        StudentResponse(
            id=s.id,
            tenant_id=s.tenant_id,
            user_id=s.user_id,
            full_name=s.user.full_name,
            email=s.user.email,
            batch_id=s.batch_id,
            section_id=s.section_id,
            roll_number=s.roll_number,
            admission_year=s.admission_year,
            status=s.status,
        )
        for s in students
    ]


@router.patch(
    "/students/{student_id}/status",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a student's status (lifecycle transition)",
    description="Only administrators, deans, or principals can perform status updates.",
)
async def update_student_status(
    student_id: uuid.UUID,
    body: StudentStatusUpdateRequest,
    current_user: Annotated[
        TokenPayload,
        Depends(require_roles(["admin", "institution_admin", "principal", "dean"])),
    ],
    service: Annotated[InstitutionService, Depends(InstitutionService)],
) -> StudentResponse:
    s = await service.update_student_status(
        current_user.tenant_uuid, student_id, body.status
    )
    return StudentResponse(
        id=s.id,
        tenant_id=s.tenant_id,
        user_id=s.user_id,
        full_name=s.user.full_name,
        email=s.user.email,
        batch_id=s.batch_id,
        section_id=s.section_id,
        roll_number=s.roll_number,
        admission_year=s.admission_year,
        status=s.status,
    )
