"""digital_assets_tables

Revision ID: 20260620_0008
Revises: 20260620_0007
Create Date: 2026-06-20 15:50:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260620_0008"
down_revision: str | None = "20260620_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. digital_assets
    op.create_table(
        "digital_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),  # BIGINT to support files > 2.1GB
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column(
            "meta_attributes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
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
            ["tenant_id", "uploaded_by"], ["users.tenant_id", "users.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_digital_assets_tenant_id"),
    )
    op.create_index(
        "idx_digital_assets_tenant",
        "digital_assets",
        ["tenant_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_digital_assets_sha256",
        "digital_assets",
        ["tenant_id", "sha256"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Enable RLS, set policy, set trigger
    op.execute("ALTER TABLE digital_assets ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_digital_assets ON digital_assets "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_digital_assets_update BEFORE UPDATE ON digital_assets "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS digital_assets CASCADE;")
