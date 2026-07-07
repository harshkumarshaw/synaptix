"""results_mark_sheets

Revision ID: b3e3a9c7b420
Revises: b3e3a9c7b419
Create Date: 2026-07-06 18:20:00.000000+05:30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b3e3a9c7b420"
down_revision: str | None = "b3e3a9c7b419"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. exam_results
    op.create_table(
        "exam_results",
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
        sa.Column("examination_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("theory_marks", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("practical_marks", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("ia_marks", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("total_marks", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("theory_grade", sa.String(length=20), nullable=True),
        sa.Column("practical_grade", sa.String(length=20), nullable=True),
        sa.Column("overall_grade", sa.String(length=20), nullable=True),
        sa.Column("grace_marks_applied", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
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
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "examination_id"],
            ["examinations.tenant_id", "examinations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["workflow_instances.tenant_id", "workflow_instances.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_exam_results_tenant_id"),
        sa.CheckConstraint(
            "status IN ('draft', 'verified', 'approved', 'published')",
            name="chk_exam_results_status",
        ),
    )

    op.create_index(
        "idx_exam_results_student_exam",
        "exam_results",
        ["tenant_id", "student_id", "examination_id"],
    )

    op.execute("ALTER TABLE exam_results ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_exam_results ON exam_results "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_exam_results_update BEFORE UPDATE ON exam_results "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # 2. exam_moderation
    op.create_table(
        "exam_moderation",
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
        sa.Column("exam_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("examiner_1_marks", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("examiner_2_marks", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("examiner_3_marks", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("moderation_method", sa.String(length=50), nullable=False),
        sa.Column("final_marks", sa.Numeric(precision=5, scale=2), nullable=False),
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
            ["tenant_id", "exam_result_id"],
            ["exam_results.tenant_id", "exam_results.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_exam_moderation_tenant_id"),
    )

    op.execute("ALTER TABLE exam_moderation ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_exam_moderation ON exam_moderation "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_exam_moderation_update BEFORE UPDATE ON exam_moderation "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # 3. mark_sheets
    op.create_table(
        "mark_sheets",
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
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("semester", sa.String(length=20), nullable=True),
        sa.Column("pdf_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qr_verification_code", sa.String(length=100), nullable=False, unique=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["tenant_id", "pdf_asset_id"],
            ["digital_assets.tenant_id", "digital_assets.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_mark_sheets_tenant_id"),
    )

    op.execute("ALTER TABLE mark_sheets ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_mark_sheets ON mark_sheets "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_mark_sheets_update BEFORE UPDATE ON mark_sheets "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # 4. question_papers
    op.create_table(
        "question_papers",
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
        sa.Column("paper_type", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
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
            ["tenant_id", "asset_id"],
            ["digital_assets.tenant_id", "digital_assets.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_question_papers_tenant_id"),
        sa.CheckConstraint(
            "paper_type IN ('theory', 'practical', 'viva')",
            name="chk_question_papers_paper_type",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'locked')",
            name="chk_question_papers_status",
        ),
    )

    op.execute("ALTER TABLE question_papers ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_question_papers ON question_papers "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_question_papers_update BEFORE UPDATE ON question_papers "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )


def downgrade() -> None:
    op.drop_table("question_papers")
    op.drop_table("mark_sheets")
    op.drop_table("exam_moderation")
    op.drop_table("exam_results")
