"""phase2_admissions

Revision ID: 20260620_0013
Revises: 20260620_0012
Create Date: 2026-06-20 19:00:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260620_0013"
down_revision: str | None = "20260620_0012"
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

    # 1. Create admission_applications table
    op.create_table(
        "admission_applications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_number", sa.String(50), nullable=False),
        sa.Column("student_name", sa.String(150), nullable=False),
        sa.Column("applied_for_program_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "applied_for_program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_admission_applications_id"),
        sa.UniqueConstraint(
            "tenant_id", "application_number", name="uq_admission_applications_number"
        ),
    )
    finalize_table("admission_applications")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS admission_applications CASCADE;")
