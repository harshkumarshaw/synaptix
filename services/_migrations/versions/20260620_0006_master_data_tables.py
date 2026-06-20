"""master_data_tables

Revision ID: 20260620_0006
Revises: 20260620_0005
Create Date: 2026-06-20 15:40:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260620_0006"
down_revision: str | None = "20260620_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add unique constraint on (tenant_id, id) for curricula to support composite FK
    op.create_unique_constraint("uq_curricula_tenant_id", "curricula", ["tenant_id", "id"])

    # 1. master_data_entities
    op.create_table(
        "master_data_entities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("extra_attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_master_data_entities_tenant_id"),
    )

    op.create_index(
        "idx_master_data_entities_tenant",
        "master_data_entities",
        ["tenant_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_master_data_entities_tenant_category_code",
        "master_data_entities",
        ["tenant_id", "category", "code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Enable RLS, set policy, trigger
    op.execute("ALTER TABLE master_data_entities ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_master_data_entities ON master_data_entities "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_master_data_entities_update BEFORE UPDATE ON master_data_entities "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS master_data_entities CASCADE;")
    op.drop_constraint("uq_curricula_tenant_id", "curricula")
