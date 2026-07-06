"""phase2_attendance_and_leave

Revision ID: 20260620_0011
Revises: 20260620_0010
Create Date: 2026-06-20 18:00:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260620_0011"
down_revision: str | None = "20260620_0010"
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

    # 1. Alter courses table to add subject_code
    op.add_column("courses", sa.Column("subject_code", sa.String(50), nullable=True))
    # Backfill subject_code from course code's prefix (e.g. "ANAT-101" -> "ANAT")
    op.execute("UPDATE courses SET subject_code = SPLIT_PART(code, '-', 1)")
    op.alter_column("courses", "subject_code", nullable=False)
    # 2. Alter programs table to add Unique constraint
    op.create_unique_constraint("uq_programs_tenant_id", "programs", ["tenant_id", "id"])

    # 3. Create placeholder internship_rotations table
    op.create_table(
        "internship_rotations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.UniqueConstraint("tenant_id", "id", name="uq_internship_rotations_tenant_id"),
    )
    finalize_table("internship_rotations")

    # 4. Create leave_requests table (so attendance can reference it)
    op.create_table(
        "leave_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rotation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("leave_type", sa.String(30), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
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
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "rotation_id"],
            ["internship_rotations.tenant_id", "internship_rotations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["workflow_instances.tenant_id", "workflow_instances.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_leave_requests_tenant_id"),
        sa.CheckConstraint(
            "leave_type IN ('medical', 'academic', 'casual', 'other')",
            name="chk_leave_requests_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="chk_leave_requests_status",
        ),
    )
    op.create_index(
        "idx_leave_requests_student",
        "leave_requests",
        ["tenant_id", "student_id", "status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    finalize_table("leave_requests")

    # 5. Create attendance table
    op.create_table(
        "attendance",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("leave_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attendance_category", sa.String(30), nullable=False),
        sa.Column("professional_phase", sa.String(20), nullable=False),
        sa.Column("method", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("geo_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("geo_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("qr_token", sa.String(255), nullable=True),
        sa.Column("exemption_batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "marked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("original_marked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
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
            ["tenant_id", "event_id"], ["events.tenant_id", "events.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "session_id"], ["sessions.tenant_id", "sessions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "leave_request_id"],
            ["leave_requests.tenant_id", "leave_requests.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reviewed_by"], ["users.tenant_id", "users.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_attendance_tenant_id"),
        sa.UniqueConstraint(
            "tenant_id", "event_id", "student_id", name="uq_attendance_event_student"
        ),
        sa.CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused', 'medical', 'official_duty', 'exempt')",
            name="chk_attendance_status",
        ),
        sa.CheckConstraint(
            "attendance_category IN ('theory', 'practical', 'clinical', 'doap', 'ece', 'aetcom', 'foundation_course', 'elective')",
            name="chk_attendance_category",
        ),
        sa.CheckConstraint(
            "professional_phase IN ('Phase I', 'Phase II', 'Phase III Part I', 'Phase III Part II')",
            name="chk_attendance_professional_phase",
        ),
        sa.CheckConstraint(
            "method IN ('manual', 'qr', 'rfid', 'face', 'gps', 'biometric')",
            name="chk_attendance_method",
        ),
    )
    op.create_index(
        "idx_attendance_student_event",
        "attendance",
        ["tenant_id", "student_id", "event_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    finalize_table("attendance")

    # 6. Create attendance_summary table
    op.create_table(
        "attendance_summary",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("professional_phase", sa.String(20), nullable=False),
        sa.Column("attendance_category", sa.String(30), nullable=False),
        sa.Column("sessions_conducted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sessions_present", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sessions_excused", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sessions_official_duty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sessions_medical", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "attendance_pct",
            sa.Numeric(5, 2),
            sa.Computed(
                """
                CASE
                    WHEN sessions_conducted = 0 THEN 0.00
                    ELSE ROUND(
                        100.0 * (sessions_present + sessions_excused + sessions_official_duty + sessions_medical)::numeric / sessions_conducted,
                        2
                    )
                END
                """,
                persisted=True,
            ),
        ),
        sa.Column(
            "last_recalculated_at",
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
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "course_id"], ["courses.tenant_id", "courses.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint(
            "tenant_id", "student_id", "course_id", "professional_phase", "attendance_category"
        ),
    )
    finalize_table("attendance_summary")

    # 7. Create attendance_exemptions table
    op.create_table(
        "attendance_exemptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exemption_batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=False),
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
            ["tenant_id", "event_id"], ["events.tenant_id", "events.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "approved_by"], ["users.tenant_id", "users.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_attendance_exemptions_tenant_id"),
    )
    finalize_table("attendance_exemptions")

    # 8. Create attendance_accommodations table
    op.create_table(
        "attendance_accommodations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=False),
        sa.Column("attendance_category", sa.String(30), nullable=True),
        sa.Column("theory_threshold_override", sa.Numeric(5, 2), nullable=True),
        sa.Column("practical_threshold_override", sa.Numeric(5, 2), nullable=True),
        sa.Column("medical_certificate_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "medical_certificate_asset_id"],
            ["digital_assets.tenant_id", "digital_assets.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["workflow_instances.tenant_id", "workflow_instances.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_attendance_accommodations_tenant_id"),
        sa.CheckConstraint(
            "theory_threshold_override <= 75.00", name="chk_accommodations_theory_limit"
        ),
        sa.CheckConstraint(
            "practical_threshold_override <= 80.00", name="chk_accommodations_practical_limit"
        ),
    )
    finalize_table("attendance_accommodations")

    # 9. Create subject_attendance_summary view
    op.execute("""
        CREATE VIEW subject_attendance_summary AS
        SELECT
            a.tenant_id,
            a.student_id,
            c.subject_code,
            a.attendance_category,
            SUM(a.sessions_conducted) AS total_conducted,
            SUM(a.sessions_present + a.sessions_excused + a.sessions_official_duty + a.sessions_medical) AS total_attended,
            CASE WHEN SUM(a.sessions_conducted) = 0 THEN 0.00
                 ELSE ROUND(100.0 * SUM(a.sessions_present + a.sessions_excused + a.sessions_official_duty + a.sessions_medical)::numeric / SUM(a.sessions_conducted), 2)
            END AS aggregate_pct,
            MAX(a.last_recalculated_at) AS last_recalculated_at
        FROM attendance_summary a
        JOIN courses c ON c.tenant_id = a.tenant_id AND c.id = a.course_id
        GROUP BY a.tenant_id, a.student_id, c.subject_code, a.attendance_category;
        """)

    # 10. Register Triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_verify_attendance_session_event()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.session_id IS NOT NULL THEN
                IF NOT EXISTS (
                    SELECT 1 FROM sessions
                    WHERE id = NEW.session_id
                      AND tenant_id = NEW.tenant_id
                      AND event_id = NEW.event_id
                ) THEN
                    RAISE EXCEPTION 'session_id % does not belong to event_id %', NEW.session_id, NEW.event_id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
    op.execute("""
        CREATE TRIGGER trg_verify_attendance_session_event
        BEFORE INSERT OR UPDATE ON attendance
        FOR EACH ROW EXECUTE FUNCTION fn_verify_attendance_session_event();
        """)

    op.execute("""
        CREATE OR REPLACE FUNCTION fn_sync_attendance_to_foundation_course()
        RETURNS TRIGGER AS $$
        DECLARE
            v_signoff TIMESTAMPTZ;
            v_req_hours NUMERIC(4,2);
            v_comp_hours NUMERIC(4,2);
            v_student_id UUID;
            v_tenant_id UUID;
        BEGIN
            v_student_id := COALESCE(NEW.student_id, OLD.student_id);
            v_tenant_id := COALESCE(NEW.tenant_id, OLD.tenant_id);

            SELECT COALESCE(SUM((EXTRACT(EPOCH FROM (e.end_time - e.start_time))/3600))::numeric(4,2), 0.00)
            INTO v_comp_hours
            FROM attendance a
            JOIN events e ON e.tenant_id = a.tenant_id AND e.id = a.event_id
            WHERE a.tenant_id = v_tenant_id
              AND a.student_id = v_student_id
              AND a.attendance_category = 'foundation_course'
              AND a.status IN ('present', 'excused', 'medical', 'official_duty')
              AND e.status = 'conducted'
              AND a.deleted_at IS NULL;

            SELECT signoff_received_at, required_hours
            INTO v_signoff, v_req_hours
            FROM foundation_course_records
            WHERE tenant_id = v_tenant_id
              AND student_id = v_student_id;

            IF v_signoff IS NOT NULL AND v_comp_hours < v_req_hours THEN
                INSERT INTO audit_log (tenant_id, actor_id, action, resource_type, resource_id, original_values, new_values)
                VALUES (
                    v_tenant_id,
                    COALESCE(NEW.updated_by, NEW.created_by),
                    'COMPLIANCE_INCIDENT',
                    'foundation_course_exemption',
                    v_student_id,
                    jsonb_build_object('signoff_received_at', v_signoff, 'hours', v_req_hours),
                    jsonb_build_object('warning', 'Completed hours dropped below required limit post-signoff', 'new_hours', v_comp_hours)
                );
            END IF;

            UPDATE foundation_course_records
            SET completed_hours = v_comp_hours,
                is_completed = (v_comp_hours >= required_hours)
            WHERE tenant_id = v_tenant_id
              AND student_id = v_student_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
    op.execute("""
        CREATE TRIGGER trg_attendance_foundation_sync
        AFTER INSERT OR UPDATE OR DELETE ON attendance
        FOR EACH ROW EXECUTE FUNCTION fn_sync_attendance_to_foundation_course();
        """)

    op.execute("""
        CREATE OR REPLACE FUNCTION fn_sync_attendance_to_aetcom()
        RETURNS TRIGGER AS $$
        DECLARE
            v_student_id UUID;
            v_tenant_id UUID;
            v_session_id UUID;
            v_competency_code VARCHAR(50);
        BEGIN
            v_student_id := COALESCE(NEW.student_id, OLD.student_id);
            v_tenant_id := COALESCE(NEW.tenant_id, OLD.tenant_id);
            v_session_id := COALESCE(NEW.session_id, OLD.session_id);

            IF COALESCE(NEW.attendance_category, OLD.attendance_category) = 'aetcom' AND
               COALESCE(NEW.status, OLD.status) IN ('present', 'excused', 'medical', 'official_duty') AND
               COALESCE(NEW.deleted_at, OLD.deleted_at) IS NULL THEN

                IF v_session_id IS NOT NULL THEN
                    SELECT lp.competency_code INTO v_competency_code
                    FROM sessions s
                    JOIN lesson_plans lp ON lp.tenant_id = s.tenant_id AND lp.id = s.lesson_plan_id
                    WHERE s.tenant_id = v_tenant_id AND s.id = v_session_id;

                    IF v_competency_code IS NOT NULL THEN
                        UPDATE aetcom_records
                        SET status = 'reflection_submitted'
                        WHERE tenant_id = v_tenant_id
                          AND student_id = v_student_id
                          AND competency_code = v_competency_code
                          AND status = 'pending';
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
    op.execute("""
        CREATE TRIGGER trg_attendance_aetcom_sync
        AFTER INSERT OR UPDATE ON attendance
        FOR EACH ROW EXECUTE FUNCTION fn_sync_attendance_to_aetcom();
        """)

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
    op.execute("""
        CREATE TRIGGER trg_events_after_insert_leave
        AFTER INSERT ON events
        FOR EACH ROW EXECUTE FUNCTION fn_events_after_insert_leave();
        """)


def downgrade() -> None:
    # Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trg_events_after_insert_leave ON events CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS fn_events_after_insert_leave CASCADE;")
    op.execute("DROP TRIGGER IF EXISTS trg_attendance_aetcom_sync ON attendance CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS fn_sync_attendance_to_aetcom CASCADE;")
    op.execute("DROP TRIGGER IF EXISTS trg_attendance_foundation_sync ON attendance CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS fn_sync_attendance_to_foundation_course CASCADE;")
    op.execute("DROP TRIGGER IF EXISTS trg_verify_attendance_session_event ON attendance CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS fn_verify_attendance_session_event CASCADE;")

    # Drop view
    op.execute("DROP VIEW IF EXISTS subject_attendance_summary CASCADE;")

    # Drop tables
    op.execute("DROP TABLE IF EXISTS attendance_accommodations CASCADE;")
    op.execute("DROP TABLE IF EXISTS attendance_exemptions CASCADE;")
    op.execute("DROP TABLE IF EXISTS attendance_summary CASCADE;")
    op.execute("DROP TABLE IF EXISTS attendance CASCADE;")
    op.execute("DROP TABLE IF EXISTS leave_requests CASCADE;")
    op.execute("DROP TABLE IF EXISTS internship_rotations CASCADE;")

    # Revert course alterations
    op.drop_column("courses", "subject_code")

    # Revert program alterations
    op.drop_constraint("uq_programs_tenant_id", "programs")
