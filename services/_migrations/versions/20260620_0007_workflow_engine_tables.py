"""workflow_engine_tables

Revision ID: 20260620_0007
Revises: 20260620_0006
Create Date: 2026-06-20 15:45:00.000000+05:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '20260620_0007'
down_revision: Union[str, None] = '20260620_0006'
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

    # Add unique constraint on (tenant_id, id) for users to support composite FKs
    op.create_unique_constraint("uq_users_tenant_id", "users", ["tenant_id", "id"])

    # 1. workflow_definitions
    op.create_table(
        "workflow_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_workflow_definitions_tenant_id"),
    )
    op.create_index("idx_workflow_definitions_tenant", "workflow_definitions", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index(
        "uq_workflow_definitions_tenant_code_version",
        "workflow_definitions",
        ["tenant_id", "code", "version"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.create_index(
        "uq_workflow_definitions_current",
        "workflow_definitions",
        ["tenant_id", "code"],
        unique=True,
        postgresql_where=sa.text("is_current = TRUE AND deleted_at IS NULL")
    )
    finalize_table("workflow_definitions")

    # 2. workflow_instances
    op.create_table(
        "workflow_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_step", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("current_assignee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("current_assignee_role", sa.String(50), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("history", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "definition_id"], ["workflow_definitions.tenant_id", "workflow_definitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "current_assignee_id"], ["users.tenant_id", "users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_workflow_instances_tenant_id"),
        sa.CheckConstraint("entity_type IN ('leave_request', 'lesson_plan_approval', 'result_moderation', 'exemption_grant')", name="chk_workflow_instances_entity_type"),
    )
    op.create_index("idx_workflow_instances_tenant", "workflow_instances", ["tenant_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_workflow_instances_entity", "workflow_instances", ["entity_type", "entity_id"])
    op.create_index(
        "uq_workflow_instances_active",
        "workflow_instances",
        ["tenant_id", "entity_type", "entity_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('approved', 'rejected', 'cancelled') AND deleted_at IS NULL")
    )
    finalize_table("workflow_instances")

    # 3. workflow_transitions
    op.create_table(
        "workflow_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_step", sa.String(50), nullable=False),
        sa.Column("to_step", sa.String(50), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "instance_id"], ["workflow_instances.tenant_id", "workflow_instances.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "actor_id"], ["users.tenant_id", "users.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_workflow_transitions_tenant", "workflow_transitions", ["tenant_id"])
    op.create_index("idx_workflow_transitions_instance", "workflow_transitions", ["instance_id"])
    
    # RLS & policy for transitions (it is append-only, but enable RLS)
    op.execute("ALTER TABLE workflow_transitions ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_workflow_transitions ON workflow_transitions "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )

    # Database trigger to append transitions to workflow_instances.history JSONB cache
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_workflow_transitions_insert_history()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE workflow_instances
            SET history = history || jsonb_build_array(
                jsonb_build_object(
                    'transition_id', NEW.id,
                    'from_step', NEW.from_step,
                    'to_step', NEW.to_step,
                    'actor_id', NEW.actor_id,
                    'comment', NEW.comment,
                    'created_at', NEW.created_at
                )
            )
            WHERE id = NEW.instance_id AND tenant_id = NEW.tenant_id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_workflow_transitions_insert
        AFTER INSERT ON workflow_transitions
        FOR EACH ROW
        EXECUTE FUNCTION fn_workflow_transitions_insert_history();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_workflow_transitions_insert ON workflow_transitions;")
    op.execute("DROP FUNCTION IF EXISTS fn_workflow_transitions_insert_history();")
    op.execute("DROP TABLE IF EXISTS workflow_transitions CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_instances CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_definitions CASCADE;")
    op.drop_constraint("uq_users_tenant_id", "users")
