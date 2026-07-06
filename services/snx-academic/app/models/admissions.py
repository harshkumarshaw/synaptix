import uuid

from sqlalchemy import ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class AdmissionApplication(TenantScopedBase):
    """Admission application record (placeholder)."""

    __tablename__ = "admission_applications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_admission_applications_id"),
        UniqueConstraint(
            "tenant_id", "application_number", name="uq_admission_applications_number"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "applied_for_program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
    )

    application_number: Mapped[str] = mapped_column(String(50), nullable=False)
    student_name: Mapped[str] = mapped_column(String(150), nullable=False)
    applied_for_program_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
