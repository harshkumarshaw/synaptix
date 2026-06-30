"""phase2_elective_allocation_runs

Adds:
  - elective_allocation_runs table (ADR-034 audit trail for each allocation execution)
  - elective_allocations.allocation_run_id FK to elective_allocation_runs
  - elective_allocations.allocation_method column ('rank_1'..'rank_10' | 'manual' | 'fcfs')
  - student_elective_preferences.submitted_at column (for FCFS ordering and tie-breaking)

Revision ID: 20260630_0014
Revises: 20260620_0013
Create Date: 2026-06-30 16:45:00.000000+05:30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260630_0014"
down_revision: str | None = "20260620_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Create elective_allocation_runs table
    #    One row per admin-triggered allocation run (live or dry-run).
    #    ADR-034: Every allocation run (FCFS or Ranked) must produce an audit row.
    # -------------------------------------------------------------------------
    op.create_table(
        "elective_allocation_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block", sa.String(10), nullable=False),
        sa.Column("algorithm_used", sa.String(20), nullable=False),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("is_dry_run", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("force_reallocate", sa.String(20), nullable=True),  # 'additive' | 'full' | NULL
        sa.Column("total_students", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_allocated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_unallocated_pending_review", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("run_duration_ms", sa.Integer(), nullable=True),
        # JSONB summary: {"rank_1": 9, "rank_2": 1, "manual": 0}
        sa.Column(
            "results_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="'{}'",
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
        # Composite FK: tenant must exist
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT",
        ),
        # Composite FK: triggered_by must be a user in this tenant
        sa.ForeignKeyConstraint(
            ["tenant_id", "triggered_by"],
            ["users.tenant_id", "users.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_elective_allocation_runs_tenant_id"),
        sa.CheckConstraint(
            "block IN ('Block 1', 'Block 2')", name="chk_allocation_runs_block"
        ),
        sa.CheckConstraint(
            "algorithm_used IN ('fcfs', 'ranked')", name="chk_allocation_runs_algorithm"
        ),
        sa.CheckConstraint(
            "force_reallocate IN ('additive', 'full') OR force_reallocate IS NULL",
            name="chk_allocation_runs_force_reallocate",
        ),
    )

    # Indexes for query patterns
    op.create_index(
        "idx_allocation_runs_tenant_block",
        "elective_allocation_runs",
        ["tenant_id", "curriculum_id", "block", "triggered_at"],
    )

    # RLS + updated_at trigger (consistent with all other tables)
    op.execute("ALTER TABLE elective_allocation_runs ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_elective_allocation_runs ON elective_allocation_runs "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_elective_allocation_runs_update "
        "BEFORE UPDATE ON elective_allocation_runs "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # -------------------------------------------------------------------------
    # 2. Add allocation_run_id column to elective_allocations
    #    Links each allocation back to the run that produced it.
    #    NULL allowed for manual allocations created outside an automated run.
    # -------------------------------------------------------------------------
    op.add_column(
        "elective_allocations",
        sa.Column("allocation_run_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_elective_allocations_run",
        "elective_allocations",
        "elective_allocation_runs",
        ["allocation_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_elective_allocations_run_id",
        "elective_allocations",
        ["allocation_run_id"],
        postgresql_where=sa.text("allocation_run_id IS NOT NULL"),
    )

    # -------------------------------------------------------------------------
    # 3. Add allocation_method column to elective_allocations
    #    Records HOW the student was allocated: rank_1..rank_10, fcfs, manual.
    # -------------------------------------------------------------------------
    op.add_column(
        "elective_allocations",
        sa.Column("allocation_method", sa.String(20), nullable=True),
    )
    op.create_check_constraint(
        "chk_elective_allocations_method",
        "elective_allocations",
        "allocation_method IN ('rank_1','rank_2','rank_3','rank_4','rank_5',"
        "'rank_6','rank_7','rank_8','rank_9','rank_10','fcfs','manual') "
        "OR allocation_method IS NULL",
    )

    # -------------------------------------------------------------------------
    # 4. Add submitted_at column to student_elective_preferences
    #    Required for FCFS ordering (submit time) and ranked tie-breaking.
    #    Default NOW() so existing rows (if any) get current timestamp.
    # -------------------------------------------------------------------------
    op.add_column(
        "student_elective_preferences",
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_student_elective_preferences_submitted",
        "student_elective_preferences",
        ["tenant_id", "student_id", "block", "submitted_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    # Reverse in opposite order

    # 4. Remove submitted_at from student_elective_preferences
    op.drop_index(
        "idx_student_elective_preferences_submitted",
        table_name="student_elective_preferences",
    )
    op.drop_column("student_elective_preferences", "submitted_at")

    # 3. Remove allocation_method from elective_allocations
    op.drop_constraint("chk_elective_allocations_method", "elective_allocations", type_="check")
    op.drop_column("elective_allocations", "allocation_method")

    # 2. Remove allocation_run_id from elective_allocations
    op.drop_index("idx_elective_allocations_run_id", table_name="elective_allocations")
    op.drop_constraint("fk_elective_allocations_run", "elective_allocations", type_="foreignkey")
    op.drop_column("elective_allocations", "allocation_run_id")

    # 1. Drop elective_allocation_runs
    op.execute("DROP TRIGGER IF EXISTS trg_elective_allocation_runs_update ON elective_allocation_runs;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_elective_allocation_runs ON elective_allocation_runs;")
    op.drop_index("idx_allocation_runs_tenant_block", table_name="elective_allocation_runs")
    op.drop_table("elective_allocation_runs")
