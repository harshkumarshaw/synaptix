"""phase1b_academic_tables

Revision ID: 20260620_0009
Revises: 20260620_0008
Create Date: 2026-06-20 16:40:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260620_0009"
down_revision: str | None = "20260620_0008"
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

    # 1. Alter courses table to add default_attendance_category
    op.add_column(
        "courses",
        sa.Column(
            "default_attendance_category", sa.String(30), nullable=False, server_default="theory"
        ),
    )
    op.create_check_constraint(
        "chk_courses_default_attendance_category",
        "courses",
        sa.text(
            "default_attendance_category IN ('theory', 'practical', 'clinical', 'doap', 'ece', 'aetcom', 'foundation_course', 'elective')"
        ),
    )

    # 2. Add unique constraints on existing referenced tables to support composite FKs
    op.create_unique_constraint("uq_courses_tenant_id", "courses", ["tenant_id", "id"])
    op.create_unique_constraint("uq_batches_tenant_id", "batches", ["tenant_id", "id"])
    op.create_unique_constraint(
        "uq_academic_years_tenant_id", "academic_years", ["tenant_id", "id"]
    )
    op.create_unique_constraint("uq_faculty_tenant_id", "faculty", ["tenant_id", "id"])
    op.create_unique_constraint("uq_students_tenant_id", "students", ["tenant_id", "id"])

    # 3. Create events table
    op.create_table(
        "events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("attendance_category", sa.String(30), nullable=False),
        sa.Column("professional_phase", sa.String(20), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("parent_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_by", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["tenant_id", "batch_id"], ["batches.tenant_id", "batches.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "parent_event_id"], ["events.tenant_id", "events.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "cancelled_by"], ["users.tenant_id", "users.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_events_tenant_id"),
        sa.CheckConstraint(
            "event_type IN ('lecture', 'practical', 'doap', 'ece', 'clinical_posting', 'foundation_course', 'aetcom', 'examination')",
            name="chk_events_type",
        ),
        sa.CheckConstraint(
            "attendance_category IN ('theory', 'practical', 'clinical', 'doap', 'ece', 'aetcom', 'foundation_course', 'elective')",
            name="chk_events_attendance_category",
        ),
        sa.CheckConstraint(
            "professional_phase IN ('Phase I', 'Phase II', 'Phase III Part I', 'Phase III Part II')",
            name="chk_events_professional_phase",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'conducted', 'cancelled', 'rescheduled')",
            name="chk_events_status",
        ),
    )
    op.create_index(
        "idx_events_batch_date",
        "events",
        ["tenant_id", "batch_id", "date"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_events_year_phase",
        "events",
        ["tenant_id", "academic_year_id", "professional_phase"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_events_status",
        "events",
        ["tenant_id", "status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    finalize_table("events")

    # 4. Create event_faculty join table
    op.create_table(
        "event_faculty",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.UniqueConstraint(
            "tenant_id", "event_id", "faculty_id", name="uq_event_faculty_composite"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "event_id"], ["events.tenant_id", "events.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "faculty_id"], ["faculty.tenant_id", "faculty.id"], ondelete="RESTRICT"
        ),
    )
    finalize_table("event_faculty")

    # 5. Create event_courses join table
    op.create_table(
        "event_courses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.UniqueConstraint(
            "tenant_id", "event_id", "course_id", name="uq_event_courses_composite"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "event_id"], ["events.tenant_id", "events.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "course_id"], ["courses.tenant_id", "courses.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "uq_event_courses_primary",
        "event_courses",
        ["tenant_id", "event_id"],
        unique=True,
        postgresql_where=sa.text("is_primary = TRUE"),
    )
    finalize_table("event_courses")

    # 6. Create lesson_plans table
    op.create_table(
        "lesson_plans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("topic", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("estimated_hours", sa.Numeric(4, 2), nullable=False, server_default="1.0"),
        sa.Column("competency_code", sa.String(50), nullable=True),
        sa.Column("nmc_competency_level", sa.String(2), nullable=False),
        sa.Column("is_core", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
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
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "course_id"], ["courses.tenant_id", "courses.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["workflow_instances.tenant_id", "workflow_instances.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_lesson_plans_tenant_id"),
        sa.CheckConstraint(
            "nmc_competency_level IN ('K', 'KH', 'SH', 'P')",
            name="chk_lesson_plans_competency_level",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'pending_approval', 'approved', 'rejected')",
            name="chk_lesson_plans_status",
        ),
    )
    op.create_index(
        "idx_lesson_plans_course_status",
        "lesson_plans",
        ["tenant_id", "course_id", "status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_lesson_plans_curriculum_comp",
        "lesson_plans",
        ["tenant_id", "curriculum_id", "competency_code"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_lesson_plans_current_version",
        "lesson_plans",
        ["tenant_id", "course_id", "curriculum_id", "code"],
        unique=True,
        postgresql_where=sa.text("is_current = TRUE AND deleted_at IS NULL"),
    )
    finalize_table("lesson_plans")

    # 7. Create sessions table
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_reason", sa.Text(), nullable=True),
        sa.Column(
            "conducted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("actual_hours", sa.Numeric(4, 2), nullable=False, server_default="1.0"),
        sa.Column("remarks", sa.Text(), nullable=True),
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
            ["tenant_id", "event_id"], ["events.tenant_id", "events.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "lesson_plan_id"],
            ["lesson_plans.tenant_id", "lesson_plans.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_sessions_tenant_id"),
    )
    op.create_index(
        "idx_sessions_event",
        "sessions",
        ["tenant_id", "event_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    finalize_table("sessions")

    # 8. Create session_faculty join table
    op.create_table(
        "session_faculty",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.UniqueConstraint(
            "tenant_id", "session_id", "faculty_id", name="uq_session_faculty_composite"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "session_id"], ["sessions.tenant_id", "sessions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "faculty_id"], ["faculty.tenant_id", "faculty.id"], ondelete="RESTRICT"
        ),
    )
    finalize_table("session_faculty")

    # 9. Create curriculum_migration_audits table
    op.create_table(
        "curriculum_migration_audits",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "migrated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("migration_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "from_curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "to_curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "approved_by"], ["users.tenant_id", "users.id"], ondelete="RESTRICT"
        ),
    )
    finalize_table("curriculum_migration_audits")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS curriculum_migration_audits CASCADE;")
    op.execute("DROP TABLE IF EXISTS session_faculty CASCADE;")
    op.execute("DROP TABLE IF EXISTS sessions CASCADE;")
    op.execute("DROP TABLE IF EXISTS lesson_plans CASCADE;")
    op.execute("DROP TABLE IF EXISTS event_courses CASCADE;")
    op.execute("DROP TABLE IF EXISTS event_faculty CASCADE;")
    op.execute("DROP TABLE IF EXISTS events CASCADE;")

    op.drop_constraint("uq_students_tenant_id", "students")
    op.drop_constraint("uq_faculty_tenant_id", "faculty")
    op.drop_constraint("uq_academic_years_tenant_id", "academic_years")
    op.drop_constraint("uq_batches_tenant_id", "batches")
    op.drop_constraint("uq_courses_tenant_id", "courses")

    op.drop_constraint("chk_courses_default_attendance_category", "courses")
    op.drop_column("courses", "default_attendance_category")
