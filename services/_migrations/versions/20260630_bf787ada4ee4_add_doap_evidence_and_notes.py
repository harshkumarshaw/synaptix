"""add_doap_evidence_and_notes

Revision ID: bf787ada4ee4
Revises: 20260630_0014
Create Date: 2026-06-30 17:37:55.977737+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bf787ada4ee4"
down_revision: str | None = "20260630_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    op.add_column(
        "doap_session_records",
        sa.Column(
            "evidence_asset_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column("doap_session_records", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("doap_session_records", "notes")
    op.drop_column("doap_session_records", "evidence_asset_ids")
