import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Boolean, Numeric, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class Student(TenantScopedBase):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column()
    status: Mapped[str] = mapped_column(String(50), default="active", server_default="active")


class WorkflowInstance(TenantScopedBase):
    __tablename__ = "workflow_instances"


class MdmConfig(TenantScopedBase):
    __tablename__ = "mdm_configs"

    config_key: Mapped[str] = mapped_column(String(200), nullable=False)
    config_value: Mapped[dict[str, Any]] = mapped_column(postgresql.JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)


class LogbookAssessment(TenantScopedBase):
    __tablename__ = "logbook_assessments"

    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    subject_code: Mapped[str] = mapped_column(String(50), nullable=False)
    professional_phase: Mapped[str] = mapped_column(String(20), nullable=False)
    ia_marks_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), server_default="0.00"
    )
    ia_marks_awarded: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.00"), server_default="0.00"
    )
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class DigitalAsset(TenantScopedBase):
    """Stub for digital_assets table — file records for PDFs, images, etc."""

    __tablename__ = "digital_assets"

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    meta_attributes: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB, nullable=False, server_default="{}"
    )
