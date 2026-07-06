"""phase2_logbook_electives_doap

Revision ID: 20260620_0012
Revises: 20260620_0011
Create Date: 2026-06-20 18:30:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260620_0012"
down_revision: str | None = "20260620_0011"
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

    # 1. Create electives table
    op.create_table(
        "electives",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("block", sa.String(10), nullable=False),
        sa.Column("elective_type", sa.String(30), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="10"),
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
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_electives_tenant_id"),
        sa.UniqueConstraint("tenant_id", "curriculum_id", "code", name="uq_electives_code"),
        sa.CheckConstraint("block IN ('Block 1', 'Block 2')", name="chk_electives_block"),
        sa.CheckConstraint(
            "elective_type IN ('pre_clinical', 'para_clinical', 'clinical', 'community', 'research')",
            name="chk_electives_type",
        ),
    )
    finalize_table("electives")

    # 2. Create elective_allocations table
    op.create_table(
        "elective_allocations",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("elective_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block", sa.String(10), nullable=False),
        sa.Column(
            "allocated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("supervisor_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "elective_id"],
            ["electives.tenant_id", "electives.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "supervisor_id"], ["faculty.tenant_id", "faculty.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("tenant_id", "student_id", "elective_id"),
        sa.UniqueConstraint(
            "tenant_id", "student_id", "block", name="uq_elective_allocations_student_block"
        ),
        sa.CheckConstraint(
            "block IN ('Block 1', 'Block 2')", name="chk_elective_allocations_block"
        ),
    )
    finalize_table("elective_allocations")

    # 3. Create student_elective_preferences table
    op.create_table(
        "student_elective_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("elective_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block", sa.String(10), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "elective_id"],
            ["electives.tenant_id", "electives.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_student_elective_preferences_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_id",
            "block",
            "rank_position",
            name="uq_elective_preferences_rank",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "student_id",
            "block",
            "elective_id",
            name="uq_elective_preferences_elective",
        ),
        sa.CheckConstraint(
            "block IN ('Block 1', 'Block 2')", name="chk_elective_preferences_block"
        ),
        sa.CheckConstraint(
            "rank_position BETWEEN 1 AND 10", name="chk_elective_preferences_rank_range"
        ),
    )
    finalize_table("student_elective_preferences")

    # 4. Create logbook_entries table
    op.create_table(
        "logbook_entries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("elective_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_code", sa.String(50), nullable=True),
        sa.Column("professional_phase", sa.String(20), nullable=False),
        sa.Column("competency_code", sa.String(50), nullable=False),
        sa.Column("nmc_level", sa.String(2), nullable=False),
        sa.Column("is_core", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("activity_name", sa.String(150), nullable=False),
        sa.Column("reflection", sa.Text(), nullable=True),
        sa.Column("rating", sa.String(10), nullable=True),
        sa.Column("attempt_type", sa.String(10), nullable=True),
        sa.Column("faculty_decision", sa.String(10), nullable=True),
        sa.Column("faculty_initials", sa.String(10), nullable=True),
        sa.Column("student_initials", sa.String(10), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("backdated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("backdating_approved_by", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "elective_id"],
            ["electives.tenant_id", "electives.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "signed_off_by"], ["faculty.tenant_id", "faculty.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "backdating_approved_by"],
            ["users.tenant_id", "users.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_logbook_entries_tenant_id"),
        sa.CheckConstraint(
            "((elective_id IS NULL AND subject_code IS NOT NULL) OR (elective_id IS NOT NULL AND subject_code IS NULL))",
            name="chk_logbook_entries_elective",
        ),
        sa.CheckConstraint(
            "nmc_level IN ('K', 'KH', 'SH', 'P')", name="chk_logbook_entries_nmc_level"
        ),
        sa.CheckConstraint("rating IN ('B', 'M', 'E')", name="chk_logbook_entries_rating"),
        sa.CheckConstraint(
            "attempt_type IN ('F', 'R', 'Re')", name="chk_logbook_entries_attempt_type"
        ),
        sa.CheckConstraint(
            "faculty_decision IN ('C', 'R', 'Re')", name="chk_logbook_entries_faculty_decision"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'submitted', 'approved', 'rejected')",
            name="chk_logbook_entries_status",
        ),
    )
    finalize_table("logbook_entries")

    # 5. Create logbook_assessments table
    op.create_table(
        "logbook_assessments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_code", sa.String(50), nullable=False),
        sa.Column("professional_phase", sa.String(20), nullable=False),
        sa.Column("total_entries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_entries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ia_marks_pct", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("ia_marks_awarded", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("is_complete", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "signed_off_by"], ["faculty.tenant_id", "faculty.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_logbook_assessments_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_id",
            "subject_code",
            "professional_phase",
            name="uq_logbook_assessments_student_subject_phase",
        ),
    )
    finalize_table("logbook_assessments")

    # 6. Create doap_session_records table
    op.create_table(
        "doap_session_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("competency_code", sa.String(50), nullable=False),
        sa.Column("nmc_level", sa.String(2), nullable=False),
        sa.Column("is_core", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("stage", sa.String(10), nullable=False),
        sa.Column("rating", sa.String(10), nullable=False),
        sa.Column("attempt_type", sa.String(10), nullable=False),
        sa.Column("faculty_decision", sa.String(10), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "signed_off_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
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
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "session_id"], ["sessions.tenant_id", "sessions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "faculty_id"], ["faculty.tenant_id", "faculty.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_doap_session_records_id"),
        sa.CheckConstraint("nmc_level IN ('K', 'KH', 'SH', 'P')", name="chk_doap_nmc_level"),
        sa.CheckConstraint("stage IN ('D', 'O', 'A', 'P')", name="chk_doap_stage"),
        sa.CheckConstraint("rating IN ('B', 'M', 'E')", name="chk_doap_rating"),
        sa.CheckConstraint("attempt_type IN ('F', 'R', 'Re')", name="chk_doap_attempt_type"),
        sa.CheckConstraint(
            "faculty_decision IN ('C', 'R', 'Re')", name="chk_doap_faculty_decision"
        ),
    )
    finalize_table("doap_session_records")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS doap_session_records CASCADE;")
    op.execute("DROP TABLE IF EXISTS logbook_assessments CASCADE;")
    op.execute("DROP TABLE IF EXISTS logbook_entries CASCADE;")
    op.execute("DROP TABLE IF EXISTS student_elective_preferences CASCADE;")
    op.execute("DROP TABLE IF EXISTS elective_allocations CASCADE;")
    op.execute("DROP TABLE IF EXISTS electives CASCADE;")
