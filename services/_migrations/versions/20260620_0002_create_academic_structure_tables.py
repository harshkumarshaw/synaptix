"""create_academic_structure_tables

Revision ID: 20260620_0002
Revises: 20260620_0001
Create Date: 2026-06-20 13:51:07.247401+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260620_0002"
down_revision: str | None = "20260620_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── academic_years (tenant-scoped) ──────────────────────────────────────
    op.create_table(
        "academic_years",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.UniqueConstraint("tenant_id", "name", name="uq_academic_years_tenant_name"),
    )
    op.create_index(
        "idx_academic_years_tenant",
        "academic_years",
        ["tenant_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute("ALTER TABLE academic_years ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_academic_years ON academic_years "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_academic_years_update BEFORE UPDATE ON academic_years "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # ── programs (tenant-scoped) ───────────────────────────────────────────
    op.create_table(
        "programs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("type", sa.String(50), nullable=False, comment="professional_phase | semester"),
        sa.Column("duration_years", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.UniqueConstraint("tenant_id", "code", name="uq_programs_tenant_code"),
    )
    op.create_index(
        "idx_programs_tenant",
        "programs",
        ["tenant_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute("ALTER TABLE programs ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_programs ON programs "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_programs_update BEFORE UPDATE ON programs "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # ── curricula (tenant-scoped) ──────────────────────────────────────────
    op.create_table(
        "curricula",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("version_code", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("program_id", "version_code", name="uq_curricula_program_version"),
    )
    op.create_index(
        "idx_curricula_tenant",
        "curricula",
        ["tenant_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_curricula_program",
        "curricula",
        ["program_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute("ALTER TABLE curricula ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_curricula ON curricula "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_curricula_update BEFORE UPDATE ON curricula "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS curricula CASCADE;")
    op.execute("DROP TABLE IF EXISTS programs CASCADE;")
    op.execute("DROP TABLE IF EXISTS academic_years CASCADE;")
