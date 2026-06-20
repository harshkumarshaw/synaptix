"""
Synaptix Database Base — Declarative base with standard columns.

Every tenant-scoped model inherits from TenantScopedBase.
Every global (non-tenant) model inherits from Base.

SQLAlchemy 2.0 Mapped[] syntax is MANDATORY. Never use old Column() syntax.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base for ALL Synaptix models.

    Every model must inherit from Base (global) or TenantScopedBase (tenant-scoped).
    """

    type_annotation_map = {
        uuid.UUID: PGUUID(as_uuid=True),
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Adds created_at and updated_at to any model.

    updated_at is automatically set by a PostgreSQL trigger (trg_*_update).
    The ORM default here is a fallback for non-trigger environments (tests).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SoftDeleteMixin:
    """Adds soft delete (deleted_at) support.

    Queries must filter WHERE deleted_at IS NULL unless explicitly accessing archived data.
    All RLS policies include this filter.
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record has been soft-deleted."""
        return self.deleted_at is not None


class TenantScopedBase(Base, TimestampMixin, SoftDeleteMixin):
    """Abstract base for ALL tenant-scoped models.

    Includes:
    - id: UUID primary key
    - tenant_id: FK to tenants.id (NON-NULLABLE, enforced by RLS)
    - created_at, updated_at: Timestamps
    - deleted_at: Soft delete support

    Usage:
        class Student(TenantScopedBase):
            __tablename__ = "students"
            ...
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )


class GlobalBase(Base, TimestampMixin):
    """Abstract base for global (non-tenant-scoped) tables.

    Use for: tenants, system_config, super_admin audit logs.
    Do NOT use this for any table that should be tenant-isolated.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
