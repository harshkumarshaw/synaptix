-- Synaptix Database Initialisation
-- Run automatically when PostgreSQL container starts for first time

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for full-text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Helper function: auto-update updated_at column
CREATE OR REPLACE FUNCTION fn_update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Helper function: block UPDATE/DELETE on audit_log
CREATE OR REPLACE FUNCTION fn_audit_log_append_only()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only — cannot modify or delete records';
END;
$$ LANGUAGE plpgsql;

-- Tenants table (must exist before any tenant-scoped table)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    domain VARCHAR(255) UNIQUE,
    type VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenants_code ON tenants(code);

CREATE TRIGGER trg_tenants_update
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- Initial tenant for development
INSERT INTO tenants (code, name, type, config)
VALUES (
    'jmn',
    'JMN Medical College & Hospital',
    'medical_college',
    jsonb_build_object(
        'address', 'Kalyani, Nadia District, West Bengal',
        'governing_body', 'NMC',
        'foundation_year', 2020,
        'curriculum_versions', jsonb_build_array('NMC_CBME_2019', 'NMC_CBME_2023')
    )
) ON CONFLICT (code) DO NOTHING;

-- Subsequent migrations handled by Alembic from packages/shared/db/migrations
