from __future__ import annotations

import uuid
from typing import Annotated

from app.schemas.master_data import (
    MasterDataEntityCreate,
    MasterDataEntityResponse,
    MasterDataEntityUpdate,
)
from app.services.master_data_service import MasterDataService
from fastapi import APIRouter, Depends, Request, status

from packages.shared.auth.dependencies import get_current_user, require_roles
from packages.shared.auth.jwt import TokenPayload
from packages.shared.auth.tenant_context import require_tenant_context

router = APIRouter(prefix="/workflow/master-data", tags=["master-data"])


@router.get(
    "",
    response_model=list[MasterDataEntityResponse],
    status_code=status.HTTP_200_OK,
    summary="List master data entities by category",
)
@require_tenant_context
async def list_entities(
    request: Request,
    category: str,
    curriculum_id: uuid.UUID | None = None,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[MasterDataService, Depends(MasterDataService)] = None,
) -> list[MasterDataEntityResponse]:
    tenant_id = request.state.tenant_id
    entities = await service.get_entities(tenant_id, category, curriculum_id)
    return [MasterDataEntityResponse.model_validate(e) for e in entities]


@router.get(
    "/{id}",
    response_model=MasterDataEntityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single master data entity details",
)
@require_tenant_context
async def get_entity(
    id: uuid.UUID,
    request: Request,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[MasterDataService, Depends(MasterDataService)] = None,
) -> MasterDataEntityResponse:
    tenant_id = request.state.tenant_id
    entity = await service.get_entity(tenant_id, id)
    return MasterDataEntityResponse.model_validate(entity)


@router.post(
    "",
    response_model=MasterDataEntityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new master data entity",
)
@require_tenant_context
async def create_entity(
    body: MasterDataEntityCreate,
    request: Request,
    current_user: Annotated[
        TokenPayload,
        Depends(require_roles(["super_admin", "institution_admin"])),
    ] = None,
    service: Annotated[MasterDataService, Depends(MasterDataService)] = None,
) -> MasterDataEntityResponse:
    tenant_id = request.state.tenant_id
    entity = await service.create_entity(tenant_id, body)
    return MasterDataEntityResponse.model_validate(entity)


@router.put(
    "/{id}",
    response_model=MasterDataEntityResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a master data entity",
)
@require_tenant_context
async def update_entity(
    id: uuid.UUID,
    body: MasterDataEntityUpdate,
    request: Request,
    current_user: Annotated[
        TokenPayload,
        Depends(require_roles(["super_admin", "institution_admin"])),
    ] = None,
    service: Annotated[MasterDataService, Depends(MasterDataService)] = None,
) -> MasterDataEntityResponse:
    tenant_id = request.state.tenant_id
    entity = await service.update_entity(tenant_id, id, body)
    return MasterDataEntityResponse.model_validate(entity)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a master data entity",
)
@require_tenant_context
async def delete_entity(
    id: uuid.UUID,
    request: Request,
    current_user: Annotated[
        TokenPayload,
        Depends(require_roles(["super_admin", "institution_admin"])),
    ] = None,
    service: Annotated[MasterDataService, Depends(MasterDataService)] = None,
) -> None:
    tenant_id = request.state.tenant_id
    await service.delete_entity(tenant_id, id)
