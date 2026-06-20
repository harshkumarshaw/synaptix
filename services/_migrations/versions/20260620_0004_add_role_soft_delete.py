"""add_role_soft_delete

Revision ID: 20260620_0004
Revises: 20260620_0003
Create Date: 2026-06-20 13:57:41.233603+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260620_0004"
down_revision: str | None = "20260620_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("roles", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_roles", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("user_roles", "deleted_at")
    op.drop_column("roles", "deleted_at")
