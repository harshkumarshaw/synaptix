from typing import Any

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class MdmConfig(TenantScopedBase):
    __tablename__ = "mdm_configs"

    config_key: Mapped[str] = mapped_column(String(200), nullable=False)
    config_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
