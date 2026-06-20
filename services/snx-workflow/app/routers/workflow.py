from __future__ import annotations

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from packages.shared.auth.dependencies import get_current_user, require_roles
from packages.shared.auth.jwt import TokenPayload
from packages.shared.auth.tenant_context import require_tenant_context

from app.schemas.workflow import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionResponse,
    WorkflowInstanceCreate,
    WorkflowInstanceResponse,
    WorkflowTransitionCreate,
)
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get(
    "/definitions",
    response_model=list[WorkflowDefinitionResponse],
    status_code=status.HTTP_200_OK,
    summary="List all workflow definitions for the tenant",
)
@require_tenant_context
async def list_definitions(
    request: Request,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[WorkflowService, Depends(WorkflowService)] = None,
) -> list[WorkflowDefinitionResponse]:
    tenant_id = request.state.tenant_id
    definitions = await service.get_definitions(tenant_id)
    return [WorkflowDefinitionResponse.model_validate(d) for d in definitions]


@router.get(
    "/definitions/{id}",
    response_model=WorkflowDefinitionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single workflow definition details",
)
@require_tenant_context
async def get_definition(
    id: uuid.UUID,
    request: Request,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[WorkflowService, Depends(WorkflowService)] = None,
) -> WorkflowDefinitionResponse:
    tenant_id = request.state.tenant_id
    definition = await service.get_definition(tenant_id, id)
    return WorkflowDefinitionResponse.model_validate(definition)


@router.post(
    "/definitions",
    response_model=WorkflowDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new version of workflow definition",
)
@require_tenant_context
async def create_definition(
    body: WorkflowDefinitionCreate,
    request: Request,
    current_user: Annotated[
        TokenPayload,
        Depends(require_roles(["super_admin", "institution_admin"])),
    ] = None,
    service: Annotated[WorkflowService, Depends(WorkflowService)] = None,
) -> WorkflowDefinitionResponse:
    tenant_id = request.state.tenant_id
    definition = await service.create_definition(tenant_id, body)
    return WorkflowDefinitionResponse.model_validate(definition)


@router.post(
    "/instances",
    response_model=WorkflowInstanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow instance for an entity",
)
@require_tenant_context
async def create_instance(
    body: WorkflowInstanceCreate,
    request: Request,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[WorkflowService, Depends(WorkflowService)] = None,
) -> WorkflowInstanceResponse:
    tenant_id = request.state.tenant_id
    instance = await service.create_instance(tenant_id, body)
    return WorkflowInstanceResponse.model_validate(instance)


@router.get(
    "/instances/{id}",
    response_model=WorkflowInstanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single workflow instance details",
)
@require_tenant_context
async def get_instance(
    id: uuid.UUID,
    request: Request,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[WorkflowService, Depends(WorkflowService)] = None,
) -> WorkflowInstanceResponse:
    tenant_id = request.state.tenant_id
    instance = await service.get_instance(tenant_id, id)
    return WorkflowInstanceResponse.model_validate(instance)


@router.post(
    "/instances/{id}/transitions",
    response_model=WorkflowInstanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a transition/approval step",
)
@require_tenant_context
async def submit_transition(
    id: uuid.UUID,
    body: WorkflowTransitionCreate,
    request: Request,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[WorkflowService, Depends(WorkflowService)] = None,
) -> WorkflowInstanceResponse:
    tenant_id = request.state.tenant_id
    instance = await service.submit_transition(
        tenant_id=tenant_id,
        instance_id=id,
        to_step=body.to_step,
        comment=body.comment,
        actor_user_id=current_user.user_uuid,
        actor_roles=current_user.roles,
    )
    return WorkflowInstanceResponse.model_validate(instance)
