"""ia_aggregation_eligibility

Revision ID: b3e3a9c7b419
Revises: b3e3a9c7b418
Create Date: 2026-07-06 18:10:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b3e3a9c7b419"
down_revision: str | None = "b3e3a9c7b418"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. viva_scores
    op.create_table(
        "viva_scores",
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
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("professional_phase", sa.String(length=30), nullable=False),
        sa.Column("examiner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("max_marks", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            "conducted_at",
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
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "examiner_id"],
            ["faculty.tenant_id", "faculty.user_id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_viva_scores_tenant_id"),
    )

    op.execute("ALTER TABLE viva_scores ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_viva_scores ON viva_scores "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_viva_scores_update BEFORE UPDATE ON viva_scores "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # 2. practical_assessments
    op.create_table(
        "practical_assessments",
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
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("professional_phase", sa.String(length=30), nullable=False),
        sa.Column("examiner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("max_marks", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            "conducted_at",
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
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "examiner_id"],
            ["faculty.tenant_id", "faculty.user_id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_practical_assessments_tenant_id"),
    )

    op.execute("ALTER TABLE practical_assessments ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_practical_assessments ON practical_assessments "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_practical_assessments_update BEFORE UPDATE ON practical_assessments "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # 3. clinical_evaluations
    op.create_table(
        "clinical_evaluations",
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
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("professional_phase", sa.String(length=30), nullable=False),
        sa.Column("evaluator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("max_marks", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("posting_period", sa.String(length=50), nullable=True),
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
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "evaluator_id"],
            ["faculty.tenant_id", "faculty.user_id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_clinical_evaluations_tenant_id"),
    )

    op.execute("ALTER TABLE clinical_evaluations ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_clinical_evaluations ON clinical_evaluations "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_clinical_evaluations_update BEFORE UPDATE ON clinical_evaluations "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # 4. ia_aggregation
    op.create_table(
        "ia_aggregation",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("professional_phase", sa.String(length=30), nullable=False),
        sa.Column(
            "logbook_marks", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column(
            "viva_marks", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column(
            "practical_marks",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "clinical_marks",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_ia", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column(
            "ia_max", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column("is_eligible", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.PrimaryKeyConstraint("tenant_id", "student_id", "course_id", "professional_phase"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
    )

    op.execute("ALTER TABLE ia_aggregation ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_ia_aggregation ON ia_aggregation "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_ia_aggregation_update BEFORE UPDATE ON ia_aggregation "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # 5. exam_eligibility
    op.create_table(
        "exam_eligibility",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("examination_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_eligible", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("blocking_reasons", postgresql.JSONB(), nullable=True),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("checked_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "student_id", "examination_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "examination_id"],
            ["examinations.tenant_id", "examinations.id"],
            ondelete="CASCADE",
        ),
    )

    op.execute("ALTER TABLE exam_eligibility ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_exam_eligibility ON exam_eligibility "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )


def downgrade() -> None:
    op.drop_table("exam_eligibility")
    op.drop_table("ia_aggregation")
    op.drop_table("clinical_evaluations")
    op.drop_table("practical_assessments")
    op.drop_table("viva_scores")
