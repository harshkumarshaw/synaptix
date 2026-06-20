# Synaptix — Phase 1A Part 3: Workflow Engine, MDM & Digital Assets (snx-workflow)

## Goal
Scaffold F-02 Master Data Management (MDM), F-03 Workflow Engine, and F-07 Digital Asset Repository modules under the **`snx-workflow`** service (port `8010`). This plan incorporates all corrections, enhancements, and constraints from the technical passes.

---

## Technical Design Decisions & Constraints

> [!IMPORTANT]
> - **Directory Naming Consistency:** To match existing folders in the monorepo (`services/snx-auth`, `services/snx-academic`, `services/snx-institution`), the directory for this service will be `services/snx-workflow`.
> - **SQLAlchemy Attribute Naming:** To avoid collisions with SQLAlchemy's `Base.metadata`, the metadata column on `master_data_entities` is named `extra_attributes`. The `meta` column on `digital_assets` is named `meta_attributes`.
> - **File Size Range:** The `file_size` column in `digital_assets` is defined as `BIGINT` to support file uploads larger than 2.1GB.
> - **Tenant-Consistency Enforced Globally:** All cross-table references within this service will use composite FKs containing `tenant_id`. Target tables will be updated to include composite unique keys on `(tenant_id, id)`.
> - **Immutable Versioned Definitions with `is_current`:** `workflow_definitions` are immutable. Modifications result in a new version record. The current version is marked via `is_current` BOOLEAN flag, restricted by a partial unique index: `WHERE is_current = TRUE AND deleted_at IS NULL`.
> - **Transitions Atomicity Trigger:** Cache consistency is enforced at the database level via a trigger `trg_workflow_transitions_insert` that automatically appends the transition to the `workflow_instances.history` JSONB array whenever a row is inserted into `workflow_transitions`.
> - **Assignee & SLA Fields:** Added `current_assignee_id`, `current_assignee_role`, and `due_at` columns to `workflow_instances`.
> - **Active Instance Limit via Terminal Statuses:** A partial unique index on `(tenant_id, entity_type, entity_id)` where `status NOT IN ('approved', 'rejected', 'cancelled')` prevents duplicate concurrent active workflows.
> - **Entity Type Validation:** `entity_type` will have a CHECK constraint restricting it to `('leave_request', 'lesson_plan_approval', 'result_moderation', 'exemption_grant')`.
> - **Soft-Deleted Assignee Handling:** The workflow service will detect if an assignee is soft-deleted and automatically reassign the step to the HOD (using department HOD mapping) or fallback to role-based open assignment.
> - **Audit Trail Writes:** Every state modification (transition, definition creation, asset upload/download) will write an entry to `audit_log` (under actions like `WORKFLOW_TRANSITION`, `ASSET_UPLOAD`, `ASSET_DOWNLOAD`).
> - **MDM Scoped to Curriculum:** Option (a) is selected. `master_data_entities` will include an optional `curriculum_id` referencing `curricula(tenant_id, id)` via a composite foreign key.
> - **Local Storage Bind-Mount:** The local storage path in `docker-compose.yml` will be bind-mounted to `./storage/assets/` on the host to ensure persistence and allow backup alongside the database.
> - **SLA Enforcement:** Overdue instances tracking using `due_at` will be evaluated in Phase 2 via Celery beat. For now, the field is seeded, validated, and queried in API filters.
> - **NMC Compliance Tests Note:** There are no direct regulatory NMC rules for the generic workflow engine itself. However, downstream services (like leave and exemption approvals) will utilize this engine to satisfy regulatory constraints.

---

## Open Decisions & Contracts

> [!NOTE]
> - **Context JSONB Contract:** The `context` field in `workflow_instances` is a static **snapshot** of the entity's data captured at instance creation time. The frozen `context` JSONB snapshot must be the source of truth displayed in the approval UI to ensure auditability and legal defensibility.
> - **Storage Backup:** Host-mounted asset directories and Postgres database dumps should be backed up together nightly.

---

## Proposed Changes

### Database Migrations

#### 1. [NEW] [20260620_0006_master_data_tables.py](file:///f:/Synaptix/services/_migrations/versions/20260620_0006_master_data_tables.py)
* Table: `master_data_entities`
  - `id` UUID PRIMARY KEY
  - `tenant_id` UUID NOT NULL (FK to tenants)
  - `curriculum_id` UUID NULL
  - `category` VARCHAR(50) NOT NULL (e.g. 'leave_type', 'designation')
  - `code` VARCHAR(50) NOT NULL
  - `name` VARCHAR(100) NOT NULL
  - `extra_attributes` JSONB
  - `sort_order` INTEGER NOT NULL DEFAULT 0
  - `is_active` BOOLEAN DEFAULT TRUE
  - Standard timestamps & soft-delete columns
* Constraints & Indexes:
  - Composite unique index `uq_master_data_entities_tenant_category_code` on `(tenant_id, category, code) WHERE deleted_at IS NULL`
  - Unique constraint on `(tenant_id, id)` for composite FKs
  - Composite FK: `FOREIGN KEY (tenant_id, curriculum_id) REFERENCES curricula(tenant_id, id) ON DELETE SET NULL`
* RLS policy and trigger enabled.

#### 2. [NEW] [20260620_0007_workflow_engine_tables.py](file:///f:/Synaptix/services/_migrations/versions/20260620_0007_workflow_engine_tables.py)
* Pre-requisites:
  - Alter table `users` to add a unique constraint on `(tenant_id, id)`.
* Table: `workflow_definitions`
  - `id` UUID PRIMARY KEY
  - `tenant_id` UUID NOT NULL (FK to tenants)
  - `name` VARCHAR(100) NOT NULL
  - `code` VARCHAR(50) NOT NULL
  - `description` TEXT
  - `version` INTEGER NOT NULL DEFAULT 1
  - `is_current` BOOLEAN NOT NULL DEFAULT TRUE
  - `steps` JSONB NOT NULL
  - `is_active` BOOLEAN DEFAULT TRUE
  - Standard timestamps & soft-delete columns
  - Unique Constraint `uq_workflow_definitions_tenant_code_version` on `(tenant_id, code, version) WHERE deleted_at IS NULL`
  - Partial Unique Index `uq_workflow_definitions_current` on `(tenant_id, code) WHERE is_current = TRUE AND deleted_at IS NULL`
  - Unique constraint on `(tenant_id, id)`
* Table: `workflow_instances`
  - `id` UUID PRIMARY KEY
  - `tenant_id` UUID NOT NULL (FK to tenants)
  - `definition_id` UUID NOT NULL
  - `entity_type` VARCHAR(50) NOT NULL
  - `entity_id` UUID NOT NULL
  - `current_step` VARCHAR(50) NOT NULL
  - `status` VARCHAR(30) NOT NULL
  - `current_assignee_id` UUID NULL
  - `current_assignee_role` VARCHAR(50) NULL
  - `due_at` TIMESTAMPTZ NULL
  - `history` JSONB NOT NULL DEFAULT '[]'::jsonb (appended automatically by trigger)
  - `context` JSONB NOT NULL DEFAULT '{}'::jsonb
  - Standard timestamps & soft-delete columns
  - **Constraints:**
    - CHECK constraint: `entity_type IN ('leave_request', 'lesson_plan_approval', 'result_moderation', 'exemption_grant')`
    - Composite FKs:
      - `FOREIGN KEY (tenant_id, definition_id) REFERENCES workflow_definitions(tenant_id, id) ON DELETE RESTRICT`
      - `FOREIGN KEY (tenant_id, current_assignee_id) REFERENCES users(tenant_id, id) ON DELETE SET NULL`
    - Partial Unique Index `uq_workflow_instances_active` on `(tenant_id, entity_type, entity_id) WHERE status NOT IN ('approved', 'rejected', 'cancelled') AND deleted_at IS NULL`
    - Unique constraint on `(tenant_id, id)`
* Table: `workflow_transitions`
  - `id` UUID PRIMARY KEY
  - `tenant_id` UUID NOT NULL
  - `instance_id` UUID NOT NULL
  - `from_step` VARCHAR(50) NOT NULL
  - `to_step` VARCHAR(50) NOT NULL
  - `actor_id` UUID NOT NULL
  - `comment` TEXT NULL
  - `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, instance_id) REFERENCES workflow_instances(tenant_id, id) ON DELETE CASCADE`
    - `FOREIGN KEY (tenant_id, actor_id) REFERENCES users(tenant_id, id) ON DELETE RESTRICT`
* **Trigger definition:**
  - Create trigger function `fn_workflow_transitions_insert_history()` that appends transition rows to `workflow_instances.history`.
  - Create trigger `trg_workflow_transitions_insert` on `workflow_transitions`.
* RLS policies and triggers enabled on all tables.

#### 3. [NEW] [20260620_0008_digital_assets_tables.py](file:///f:/Synaptix/services/_migrations/versions/20260620_0008_digital_assets_tables.py)
* Table: `digital_assets`
  - `id` UUID PRIMARY KEY
  - `tenant_id` UUID NOT NULL (FK to tenants)
  - `file_name` VARCHAR(255) NOT NULL
  - `file_type` VARCHAR(100) NOT NULL
  - `file_size` BIGINT NOT NULL
  - `storage_path` VARCHAR(512) NOT NULL
  - `uploaded_by` UUID NOT NULL
  - `sha256` VARCHAR(64) NOT NULL
  - `meta_attributes` JSONB NOT NULL DEFAULT '{}'::jsonb
  - Standard timestamps & soft-delete columns
  - **Composite FK:** `FOREIGN KEY (tenant_id, uploaded_by) REFERENCES users(tenant_id, id) ON DELETE RESTRICT`
* RLS policy and trigger enabled.

---

### `snx-workflow` FastAPI Service
Scaffold files in `services/snx-workflow/`:

* `pyproject.toml`
* `Dockerfile`
* `app/main.py`
* `app/config.py`
* `app/models/` (`master_data.py`, `workflow.py`, `digital_asset.py`, `user.py`, `tenant.py`, `__init__.py`)
* `app/schemas/` (`workflow.py`, `master_data.py`, `digital_asset.py`)
* `app/services/`
  - `storage.py` — `StorageProvider` & `LocalStorageProvider`
  - `workflow_service.py` — State machine transition validation, assignee validation, soft-deleted assignee handling
  - `master_data_service.py`
  - `asset_service.py`
* `app/routers/` (`workflow.py`, `master_data.py`, `digital_asset.py`)

---

### M1 Seed Data Script

#### [NEW] [scripts/seed_m1_data.py](file:///f:/Synaptix/scripts/seed_m1_data.py)
* Database seeding script using SQLAlchemy async sessions.

---

### Docker Compose Configuration

#### [MODIFY] [docker-compose.yml](file:///f:/Synaptix/docker-compose.yml)
* Add `snx-workflow` service on port `8010`.
* Bind-mount storage volume: `- ./storage/assets:/app/storage/assets`

---

## Verification Plan

### Automated Tests
Run integration and unit tests:
```powershell
$env:PYTHONPATH="F:\Synaptix;F:\Synaptix\services\snx-workflow"
.\.venv\Scripts\pytest.exe tests/unit/workflow/test_definition_versioning.py
.\.venv\Scripts\pytest.exe tests/unit/workflow/test_transitions.py
.\.venv\Scripts\pytest.exe tests/integration/workflow/test_full_lifecycle.py
.\.venv\Scripts\pytest.exe tests/security/workflow/test_tenant_isolation.py
.\.venv\Scripts\pytest.exe tests/unit/mdm/test_master_data_service.py
.\.venv\Scripts\pytest.exe tests/unit/assets/test_asset_service.py
```
