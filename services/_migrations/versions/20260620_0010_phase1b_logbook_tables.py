"""phase1b_logbook_tables

Revision ID: 20260620_0010
Revises: 20260620_0009
Create Date: 2026-06-20 16:45:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260620_0010"
down_revision: str | None = "20260620_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Helper to enable RLS, set policy, and set trigger
    def finalize_table(table_name: str) -> None:
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY tenant_isolation_{table_name} ON {table_name} "
            f"USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
        )
        op.execute(
            f"CREATE TRIGGER trg_{table_name}_update BEFORE UPDATE ON {table_name} "
            f"FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
        )

    # 1. Create foundation_course_records table
    op.create_table(
        "foundation_course_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_name", sa.String(100), nullable=False),
        sa.Column("completed_hours", sa.Numeric(4, 2), nullable=False, server_default="0.0"),
        sa.Column("required_hours", sa.Numeric(4, 2), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("signoff_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_off_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "signed_off_by"], ["faculty.tenant_id", "faculty.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_foundation_course_records_tenant_id"),
        sa.CheckConstraint(
            "module_name IN ('orientation', 'skills_acquisition', 'professional_development', 'language_computer', 'sports_yoga', 'hospital_visits')",
            name="chk_foundation_module_name",
        ),
    )
    op.create_index(
        "idx_foundation_student_status",
        "foundation_course_records",
        ["tenant_id", "student_id", "is_completed"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    finalize_table("foundation_course_records")

    # 2. Create aetcom_records table
    op.create_table(
        "aetcom_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_code", sa.String(30), nullable=False),
        sa.Column("competency_code", sa.String(50), nullable=False),
        sa.Column("professional_phase", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reflection_text", sa.Text(), nullable=True),
        sa.Column("signed_off_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signed_off_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "signed_off_by"], ["faculty.tenant_id", "faculty.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_aetcom_records_tenant_id"),
        sa.CheckConstraint(
            "professional_phase IN ('Phase I', 'Phase II', 'Phase III Part I', 'Phase III Part II')",
            name="chk_aetcom_professional_phase",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'reflection_submitted', 'completed')", name="chk_aetcom_status"
        ),
    )
    op.create_index(
        "idx_aetcom_student_phase",
        "aetcom_records",
        ["tenant_id", "student_id", "professional_phase"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_unique_constraint(
        "uq_aetcom_records_unique_competency",
        "aetcom_records",
        ["tenant_id", "student_id", "module_code", "competency_code", "professional_phase"],
    )
    finalize_table("aetcom_records")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS aetcom_records CASCADE;")
    op.execute("DROP TABLE IF EXISTS foundation_course_records CASCADE;")
