from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class MasterDataEntityBase(BaseModel):
    category: str
    code: str
    name: str
    curriculum_id: uuid.UUID | None = None
    extra_attributes: dict[str, Any] | None = None
    sort_order: int = 0
    is_active: bool = True


class MasterDataEntityCreate(MasterDataEntityBase):
    pass


class MasterDataEntityUpdate(BaseModel):
    name: str | None = None
    curriculum_id: uuid.UUID | None = None
    extra_attributes: dict[str, Any] | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class MasterDataEntityResponse(MasterDataEntityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
