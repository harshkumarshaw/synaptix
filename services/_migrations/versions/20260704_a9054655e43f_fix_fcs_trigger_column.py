"""fix_fcs_trigger_column

Revision ID: a9054655e43f
Revises: d7ce0e58cbc0
Create Date: 2026-07-04 13:17:04.805242+05:30

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9054655e43f"
down_revision: str | None = "d7ce0e58cbc0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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
                INSERT INTO audit_log (tenant_id, actor_user_id, action, resource_type, resource_id, old_values, new_values)
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


def downgrade() -> None:
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
