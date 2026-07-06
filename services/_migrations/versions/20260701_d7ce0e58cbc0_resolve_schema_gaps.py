"""resolve_schema_gaps

Revision ID: d7ce0e58cbc0
Revises: bf787ada4ee4
Create Date: 2026-07-01 14:21:56.276940+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7ce0e58cbc0"
down_revision: str | None = "bf787ada4ee4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Attendance Soft-delete Uniqueness
    #    Drop the full unique constraint and replace with a partial unique index
    #    filtering by WHERE (deleted_at IS NULL).
    # -------------------------------------------------------------------------
    op.drop_constraint("uq_attendance_event_student", "attendance", type_="unique")
    op.create_index(
        "uq_attendance_event_student",
        "attendance",
        ["tenant_id", "event_id", "student_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # -------------------------------------------------------------------------
    # 2. Elective Preferences Soft-delete Uniqueness
    #    Drop the full unique constraints and replace with partial unique indexes
    #    filtering by WHERE (deleted_at IS NULL).
    # -------------------------------------------------------------------------
    op.drop_constraint(
        "uq_elective_preferences_rank", "student_elective_preferences", type_="unique"
    )
    op.drop_constraint(
        "uq_elective_preferences_elective", "student_elective_preferences", type_="unique"
    )

    op.create_index(
        "uq_elective_preferences_rank_partial",
        "student_elective_preferences",
        ["tenant_id", "student_id", "block", "rank_position"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_elective_preferences_elective_partial",
        "student_elective_preferences",
        ["tenant_id", "student_id", "block", "elective_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # -------------------------------------------------------------------------
    # 3. Internship Rotations Scaffold Columns
    #    Add student_id, department, start_date, end_date, leave_days_used,
    #    and status columns. Add student composite foreign key.
    # -------------------------------------------------------------------------
    op.add_column("internship_rotations", sa.Column("student_id", sa.UUID(), nullable=False))
    op.add_column(
        "internship_rotations", sa.Column("department", sa.String(length=100), nullable=False)
    )
    op.add_column("internship_rotations", sa.Column("start_date", sa.Date(), nullable=False))
    op.add_column("internship_rotations", sa.Column("end_date", sa.Date(), nullable=False))
    op.add_column(
        "internship_rotations",
        sa.Column("leave_days_used", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "internship_rotations",
        sa.Column("status", sa.String(length=30), nullable=False, server_default="scheduled"),
    )

    op.create_foreign_key(
        "fk_internship_rotations_student",
        "internship_rotations",
        "students",
        ["tenant_id", "student_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "chk_internship_rotations_status",
        "internship_rotations",
        "status IN ('scheduled', 'active', 'completed', 'cancelled')",
    )

    # 4. Recreate fn_events_after_insert_leave to match partial uniqueness index on attendance
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_events_after_insert_leave()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO attendance (
                tenant_id, student_id, event_id, session_id, leave_request_id, status,
                attendance_category, professional_phase, method, marked_at, original_marked_at
            )
            SELECT
                NEW.tenant_id, lr.student_id, NEW.id, NULL, lr.id,
                CASE WHEN lr.leave_type = 'medical' THEN 'medical'::varchar ELSE 'excused'::varchar END,
                NEW.attendance_category, NEW.professional_phase, 'manual'::varchar, NOW(), NOW()
            FROM leave_requests lr
            JOIN students s ON s.tenant_id = lr.tenant_id AND s.id = lr.student_id
            WHERE lr.tenant_id = NEW.tenant_id
              AND NEW.date >= lr.start_date AND NEW.date <= lr.end_date
              AND lr.status = 'approved'
              AND s.batch_id = NEW.batch_id
              AND s.deleted_at IS NULL
              AND lr.deleted_at IS NULL
            ON CONFLICT (tenant_id, event_id, student_id) WHERE deleted_at IS NULL DO NOTHING;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    # 4. Revert fn_events_after_insert_leave trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_events_after_insert_leave()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO attendance (
                tenant_id, student_id, event_id, session_id, leave_request_id, status,
                attendance_category, professional_phase, method, marked_at, original_marked_at
            )
            SELECT
                NEW.tenant_id, lr.student_id, NEW.id, NULL, lr.id,
                CASE WHEN lr.leave_type = 'medical' THEN 'medical'::varchar ELSE 'excused'::varchar END,
                NEW.attendance_category, NEW.professional_phase, 'manual'::varchar, NOW(), NOW()
            FROM leave_requests lr
            JOIN students s ON s.tenant_id = lr.tenant_id AND s.id = lr.student_id
            WHERE lr.tenant_id = NEW.tenant_id
              AND NEW.date >= lr.start_date AND NEW.date <= lr.end_date
              AND lr.status = 'approved'
              AND s.batch_id = NEW.batch_id
              AND s.deleted_at IS NULL
              AND lr.deleted_at IS NULL
            ON CONFLICT (tenant_id, event_id, student_id) DO NOTHING;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 3. Remove internship_rotations changes
    op.drop_constraint("chk_internship_rotations_status", "internship_rotations", type_="check")
    op.drop_constraint(
        "fk_internship_rotations_student", "internship_rotations", type_="foreignkey"
    )
    op.drop_column("internship_rotations", "status")
    op.drop_column("internship_rotations", "leave_days_used")
    op.drop_column("internship_rotations", "end_date")
    op.drop_column("internship_rotations", "start_date")
    op.drop_column("internship_rotations", "department")
    op.drop_column("internship_rotations", "student_id")

    # 2. Re-create student_elective_preferences constraints and drop indexes
    op.drop_index(
        "uq_elective_preferences_elective_partial", table_name="student_elective_preferences"
    )
    op.drop_index("uq_elective_preferences_rank_partial", table_name="student_elective_preferences")
    op.create_unique_constraint(
        "uq_elective_preferences_elective",
        "student_elective_preferences",
        ["tenant_id", "student_id", "block", "elective_id"],
    )
    op.create_unique_constraint(
        "uq_elective_preferences_rank",
        "student_elective_preferences",
        ["tenant_id", "student_id", "block", "rank_position"],
    )

    # 1. Re-create attendance constraint and drop index
    op.drop_index("uq_attendance_event_student", table_name="attendance")
    op.create_unique_constraint(
        "uq_attendance_event_student",
        "attendance",
        ["tenant_id", "event_id", "student_id"],
    )
