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

-- Subsequent migrations handled by Alembic from packages/shared/db/migrations
