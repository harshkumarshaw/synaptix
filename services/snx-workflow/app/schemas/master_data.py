from __future__ import annotations

import uuid
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class MasterDataEntityBase(BaseModel):
    category: str
    code: str
    name: str
    curriculum_id: Optional[uuid.UUID] = None
    extra_attributes: Optional[dict[str, Any]] = None
    sort_order: int = 0
    is_active: bool = True


class MasterDataEntityCreate(MasterDataEntityBase):
    pass


class MasterDataEntityUpdate(BaseModel):
    name: Optional[str] = None
    curriculum_id: Optional[uuid.UUID] = None
    extra_attributes: Optional[dict[str, Any]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class MasterDataEntityResponse(MasterDataEntityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
