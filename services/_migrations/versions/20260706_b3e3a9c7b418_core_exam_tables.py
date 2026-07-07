"""core_exam_tables

Revision ID: b3e3a9c7b418
Revises: 756453b2326d
Create Date: 2026-07-06 18:00:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b3e3a9c7b418"
down_revision: str | None = "756453b2326d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add unique constraint on faculty (tenant_id, user_id) so other tables can reference it
    op.create_unique_constraint("uq_faculty_tenant_user_id", "faculty", ["tenant_id", "user_id"])

    # 1. examinations
    op.create_table(
        "examinations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_type", sa.String(length=30), nullable=False),
        sa.Column("exam_session", sa.String(length=50), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("theory_max_marks", sa.Integer(), nullable=False),
        sa.Column("practical_max_marks", sa.Integer(), nullable=False),
        sa.Column("theory_pass_marks", sa.Integer(), nullable=False),
        sa.Column("practical_pass_marks", sa.Integer(), nullable=False),
        sa.Column("grace_marks_allowed", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="scheduled"),
        sa.Column("workflow_instance_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["workflow_instances.tenant_id", "workflow_instances.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_examinations_tenant_id"),
        sa.CheckConstraint(
            "exam_type IN ('terminal', 'professional', 'supplementary')",
            name="chk_examinations_exam_type",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'results_published')",
            name="chk_examinations_status",
        ),
    )

    op.create_index(
        "idx_examinations_course_session",
        "examinations",
        ["tenant_id", "course_id", "exam_session"],
    )
    op.create_index(
        "idx_examinations_date",
        "examinations",
        ["tenant_id", "exam_date"],
    )

    op.execute("ALTER TABLE examinations ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_examinations ON examinations "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_examinations_update BEFORE UPDATE ON examinations "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # 2. exam_schedules
    op.create_table(
        "exam_schedules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("examination_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invigilator_id", postgresql.UUID(as_uuid=True), nullable=False),
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
            ["tenant_id", "examination_id"],
            ["examinations.tenant_id", "examinations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "invigilator_id"],
            ["faculty.tenant_id", "faculty.user_id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_exam_schedules_tenant_id"),
    )

    op.execute("ALTER TABLE exam_schedules ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_exam_schedules ON exam_schedules "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_exam_schedules_update BEFORE UPDATE ON exam_schedules "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )


def downgrade() -> None:
    op.drop_table("exam_schedules")
    op.drop_table("examinations")
    op.drop_constraint("uq_faculty_tenant_user_id", "faculty")
