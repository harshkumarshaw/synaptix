from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DigitalAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    file_name: str
    file_type: str
    file_size: int
    storage_path: str
    uploaded_by: uuid.UUID
    sha256: str
    meta_attributes: dict[str, Any]
    created_at: datetime
