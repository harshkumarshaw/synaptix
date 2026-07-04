"""create_mdm_configs

Revision ID: 756453b2326d
Revises: a9054655e43f
Create Date: 2026-07-04 13:47:22.407324+05:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '756453b2326d'
down_revision: Union[str, None] = 'a9054655e43f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mdm_configs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("config_key", sa.String(length=200), nullable=False),
        sa.Column("config_value", postgresql.JSONB(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("tenant_id", "config_key", name="uq_mdm_configs_tenant_key"),
    )

    op.execute("ALTER TABLE mdm_configs ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_mdm_configs ON mdm_configs "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_mdm_configs_update BEFORE UPDATE ON mdm_configs "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )


def downgrade() -> None:
    op.drop_table("mdm_configs")

