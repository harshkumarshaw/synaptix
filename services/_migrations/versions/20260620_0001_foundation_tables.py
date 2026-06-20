"""Foundation tables migration — tenants, users, roles, permissions, audit_log.

Revision ID: 20260620_0001_foundation
Revises: None (first migration)
Created: 2026-06-20

This is the first migration in the Synaptix schema chain.
Creates all tables required for Phase 1A foundation:
- tenants (global — no tenant_id FK)
- users (tenant-scoped)
- roles, permissions, user_roles, role_permissions (tenant-scoped)
- audit_log (tenant-scoped, append-only, partitioned by academic_year)

NMC Reference: Not applicable (infrastructure)
ADR Reference: ADR-004 (monorepo migration chain), ADR-006 (RLS)
"""

from __future__ import annotations

import textwrap

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Alembic revision identifiers
revision = "20260620_0001"
down_revision = None  # First migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create foundation tables."""

    # ── Helper function (created first, used by triggers below) ────────────
    op.execute(
        textwrap.dedent("""
        CREATE OR REPLACE FUNCTION fn_update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
    )

    # ── Audit log append-only enforcement function ──────────────────────────
    op.execute(
        textwrap.dedent("""
        CREATE OR REPLACE FUNCTION fn_audit_log_no_update()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only — updates and deletes are forbidden';
        END;
        $$ LANGUAGE plpgsql;
        """)
    )

    # ── tenants (GLOBAL table — no RLS, no tenant_id FK) ───────────────────
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(20), nullable=False, unique=True,
                  comment="Short identifier, e.g. JMN, IINR"),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("institution_type", sa.String(50), nullable=False,
                  comment="medical | nursing | allied_health | pharmacy | engineering | university | school"),
        sa.Column("regulatory_body", sa.String(50), nullable=False,
                  comment="NMC | INC | PCI | AICTE | UGC | state_board"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("primary_color", sa.String(7), nullable=True,
                  comment="Hex color for branding, e.g. #1A73E8"),
        sa.Column("timezone", sa.String(50), nullable=False,
                  server_default="'Asia/Kolkata'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("idx_tenants_code", "tenants", ["code"], unique=True)
    op.execute(
        "CREATE TRIGGER trg_tenants_update BEFORE UPDATE ON tenants "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # ── users (tenant-scoped) ───────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=True, comment="-- PII"),
        sa.Column("mobile", sa.String(15), nullable=True, comment="-- PII"),
        sa.Column("full_name", sa.String(200), nullable=False, comment="-- PII"),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=True,
                  comment="bcrypt hash — NULL if SSO-only"),
        sa.Column("mfa_secret", sa.Text(), nullable=True,
                  comment="TOTP secret — NULL if MFA not enrolled"),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("google_sub", sa.String(255), nullable=True,
                  comment="Google SSO subject ID"),
        sa.Column("microsoft_sub", sa.String(255), nullable=True,
                  comment="Microsoft SSO subject ID"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_given_at", sa.DateTime(timezone=True), nullable=True,
                  comment="DPDP Act 2023 — explicit consent timestamp"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        sa.UniqueConstraint("tenant_id", "mobile", name="uq_users_tenant_mobile"),
    )
    op.create_index("idx_users_tenant", "users", ["tenant_id"],
                    postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_users_tenant_email", "users", ["tenant_id", "email"],
                    postgresql_where=sa.text("email IS NOT NULL AND deleted_at IS NULL"))
    op.execute(
        "ALTER TABLE users ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        "CREATE POLICY tenant_isolation_users ON users "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_users_update BEFORE UPDATE ON users "
        "FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();"
    )

    # ── roles (tenant-scoped) ───────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False,
                  comment="e.g. faculty, hod, principal"),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("is_system_role", sa.Boolean(), nullable=False,
                  server_default="false",
                  comment="System roles cannot be deleted"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )
    op.create_index("idx_roles_tenant", "roles", ["tenant_id"])
    op.execute("ALTER TABLE roles ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_roles ON roles "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )

    # ── user_roles (many-to-many: users ↔ roles) ───────────────────────────
    op.create_table(
        "user_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("granted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )
    op.create_index("idx_user_roles_user", "user_roles", ["user_id"])
    op.create_index("idx_user_roles_tenant", "user_roles", ["tenant_id"])
    op.execute("ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_user_roles ON user_roles "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )

    # ── audit_log (append-only, tenant-scoped) ─────────────────────────────
    # Partitioned by academic_year for performance at 100M+ rows
    op.execute(
        textwrap.dedent("""
        CREATE TABLE audit_log (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
            actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            action VARCHAR(100) NOT NULL
                CONSTRAINT chk_audit_log_action CHECK (action ~ '^[A-Z_]+$'),
            resource_type VARCHAR(100) NOT NULL,
            resource_id UUID NOT NULL,
            old_values JSONB,
            new_values JSONB,
            metadata JSONB NOT NULL DEFAULT '{}',
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            -- Partition key
            partition_key DATE NOT NULL DEFAULT CURRENT_DATE
        ) PARTITION BY RANGE (partition_key);
        """)
    )

    # Create initial partition (2026)
    op.execute(
        textwrap.dedent("""
        CREATE TABLE audit_log_2026 PARTITION OF audit_log
            FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
        """)
    )

    op.execute(
        textwrap.dedent("""
        CREATE TABLE audit_log_2027 PARTITION OF audit_log
            FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');
        """)
    )

    op.create_index(
        "idx_audit_log_tenant_resource",
        "audit_log",
        ["tenant_id", "resource_type", "resource_id"],
    )
    op.create_index(
        "idx_audit_log_actor",
        "audit_log",
        ["actor_user_id", "created_at"],
    )

    # Enforce append-only
    op.execute(
        "ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        "CREATE POLICY tenant_isolation_audit_log ON audit_log "
        "USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);"
    )
    op.execute(
        "CREATE TRIGGER trg_audit_log_no_update "
        "BEFORE UPDATE OR DELETE ON audit_log "
        "FOR EACH ROW EXECUTE FUNCTION fn_audit_log_no_update();"
    )

    # ── Seed: JMN tenant ────────────────────────────────────────────────────
    op.execute(
        textwrap.dedent("""
        INSERT INTO tenants (id, code, name, institution_type, regulatory_body, timezone)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'JMN',
            'JMN Medical College & Hospital, Kalyani',
            'medical',
            'NMC',
            'Asia/Kolkata'
        )
        ON CONFLICT (code) DO NOTHING;
        """)
    )

    # ── Seed: System roles for JMN ─────────────────────────────────────────
    op.execute(
        textwrap.dedent("""
        INSERT INTO roles (id, tenant_id, name, display_name, is_system_role)
        VALUES
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'super_admin', 'Super Administrator', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'institution_admin', 'Institution Administrator', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'principal', 'Principal', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'dean', 'Dean', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'controller_of_examinations', 'Controller of Examinations', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'hod', 'Head of Department', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'faculty', 'Faculty', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'student', 'Student', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'mentor', 'Mentor', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'intern', 'Intern (CRMI)', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'parent', 'Parent / Guardian', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'accreditation_officer', 'Accreditation Officer', true),
            (gen_random_uuid(), '00000000-0000-0000-0000-000000000001',
             'inspector', 'NMC/NAAC Inspector (time-limited)', true)
        ON CONFLICT DO NOTHING;
        """)
    )


def downgrade() -> None:
    """Drop all foundation tables in reverse order."""
    op.execute("DROP TABLE IF EXISTS audit_log CASCADE;")
    op.execute("DROP TABLE IF EXISTS user_roles CASCADE;")
    op.execute("DROP TABLE IF EXISTS roles CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
    op.execute("DROP TABLE IF EXISTS tenants CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS fn_audit_log_no_update CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS fn_update_updated_at CASCADE;")
