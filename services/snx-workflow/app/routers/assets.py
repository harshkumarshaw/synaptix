from __future__ import annotations

import contextlib
import json
import uuid
from typing import Annotated

from app.schemas.digital_asset import DigitalAssetResponse
from app.services.asset_service import AssetService
from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile, status

from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload
from packages.shared.auth.tenant_context import require_tenant_context

router = APIRouter(prefix="/workflow/assets", tags=["digital-assets"])


@router.post(
    "/upload",
    response_model=DigitalAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new digital asset",
)
@require_tenant_context
async def upload_asset(
    request: Request,
    file: UploadFile = File(...),
    meta_attributes: str | None = Form(None),
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[AssetService, Depends(AssetService)] = None,
) -> DigitalAssetResponse:
    tenant_id = request.state.tenant_id
    content = await file.read()

    parsed_meta = {}
    if meta_attributes:
        with contextlib.suppress(json.JSONDecodeError):
            parsed_meta = json.loads(meta_attributes)

    asset = await service.upload_asset(
        tenant_id=tenant_id,
        file_name=file.filename,
        content=content,
        file_type=file.content_type or "application/octet-stream",
        uploaded_by=current_user.user_uuid,
        meta_attributes=parsed_meta,
    )
    return DigitalAssetResponse.model_validate(asset)


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Download a digital asset file",
)
@require_tenant_context
async def download_asset(
    id: uuid.UUID,
    request: Request,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[AssetService, Depends(AssetService)] = None,
) -> Response:
    tenant_id = request.state.tenant_id
    content, file_name, file_type = await service.download_asset(
        tenant_id=tenant_id,
        asset_id=id,
        downloader_user_id=current_user.user_uuid,
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{file_name}"',
    }
    return Response(content=content, media_type=file_type, headers=headers)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a digital asset",
)
@require_tenant_context
async def delete_asset(
    id: uuid.UUID,
    request: Request,
    current_user: Annotated[TokenPayload, Depends(get_current_user)] = None,
    service: Annotated[AssetService, Depends(AssetService)] = None,
) -> None:
    tenant_id = request.state.tenant_id
    await service.delete_asset(
        tenant_id=tenant_id,
        asset_id=id,
        actor_user_id=current_user.user_uuid,
    )
