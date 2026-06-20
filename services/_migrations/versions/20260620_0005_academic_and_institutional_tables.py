"""academic_and_institutional_tables

Revision ID: 20260620_0005
Revises: 20260620_0004
Create Date: 2026-06-20 14:20:00.000000+05:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260620_0005'
down_revision: Union[str, None] = '20260620_0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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

    # 1. departments
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_departments_tenant_code"),
    )
    op.create_index("idx_departments_tenant", "departments", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    finalize_table("departments")

    # 2. faculty
    op.create_table(
        "faculty",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("designation", sa.String(100), nullable=False),
        sa.Column("employee_id", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "employee_id", name="uq_faculty_tenant_employee_id"),
    )
    op.create_index("idx_faculty_tenant", "faculty", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_faculty_department", "faculty", ["department_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    finalize_table("faculty")

    # 3. courses
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("curriculum_id", "code", name="uq_courses_curriculum_code"),
    )
    op.create_index("idx_courses_tenant", "courses", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_courses_curriculum", "courses", ["curriculum_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    finalize_table("courses")

    # 4. batches
    op.create_table(
        "batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "academic_year_id", "code", name="uq_batches_tenant_year_code"),
    )
    op.create_index("idx_batches_tenant", "batches", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_batches_academic_year", "batches", ["academic_year_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    finalize_table("batches")

    # 5. sections
    op.create_table(
        "sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("batch_id", "name", name="uq_sections_batch_name"),
    )
    op.create_index("idx_sections_tenant", "sections", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_sections_batch", "sections", ["batch_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    finalize_table("sections")

    # 6. students
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("roll_number", sa.String(50), nullable=False),
        sa.Column("admission_year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "roll_number", name="uq_students_tenant_roll_number"),
    )
    op.create_index("idx_students_tenant", "students", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_students_batch", "students", ["batch_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    finalize_table("students")

    # 7. timetable_slots
    op.create_table(
        "timetable_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False, comment="0=Monday, 6=Sunday"),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("name", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "day_of_week", "start_time", "end_time", name="uq_timetable_slots_time"),
    )
    op.create_index("idx_timetable_slots_tenant", "timetable_slots", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    finalize_table("timetable_slots")

    # 8. timetable_entries
    op.create_table(
        "timetable_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_number", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculty.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["slot_id"], ["timetable_slots.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_timetable_entries_tenant", "timetable_entries", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_timetable_entries_batch", "timetable_entries", ["batch_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    finalize_table("timetable_entries")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS timetable_entries CASCADE;")
    op.execute("DROP TABLE IF EXISTS timetable_slots CASCADE;")
    op.execute("DROP TABLE IF EXISTS students CASCADE;")
    op.execute("DROP TABLE IF EXISTS sections CASCADE;")
    op.execute("DROP TABLE IF EXISTS batches CASCADE;")
    op.execute("DROP TABLE IF EXISTS courses CASCADE;")
    op.execute("DROP TABLE IF EXISTS faculty CASCADE;")
    op.execute("DROP TABLE IF EXISTS departments CASCADE;")
