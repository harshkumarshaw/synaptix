from __future__ import annotations

import uuid
from typing import Any

from app.models.user import User
from sqlalchemy import BigInteger, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.shared.db.base import TenantScopedBase


class DigitalAsset(TenantScopedBase):
    __tablename__ = "digital_assets"

    file_name: Mapped[str] = mapped_column(nullable=False)
    file_type: Mapped[str] = mapped_column(nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # BIGINT
    storage_path: Mapped[str] = mapped_column(nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(nullable=False)
    meta_attributes: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=False
    )

    # Composite Foreign Key Constraints
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "uploaded_by"],
            ["users.tenant_id", "users.id"],
            ondelete="RESTRICT",
        ),
    )

    # Relationships
    uploader: Mapped[User] = relationship("User", lazy="raise")
