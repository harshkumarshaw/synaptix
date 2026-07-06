# Phase 3 Schema Specification

**Status:** Draft — R0 baseline (Examination Management)
**Created:** 2026-07-04 (Session 19)
**Last updated:** 2026-07-04

> This document is the canonical schema specification for all Phase 3 tables. It is the contract between schema design (R1) and migration files (R3).

---

## Tables Added in Phase 3

### 1. `examinations`
**ADR:** ADR-040, ADR-045

```sql
CREATE TABLE examinations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    curriculum_id UUID NOT NULL,
    course_id UUID NOT NULL,
    exam_type VARCHAR(30) NOT NULL CHECK (exam_type IN ('terminal', 'professional', 'supplementary')),
    exam_session VARCHAR(50) NOT NULL, -- e.g., 'Dec 2026'
    academic_year VARCHAR(20) NOT NULL, -- e.g., '2026-2027'
    exam_date DATE NOT NULL,
    theory_max_marks INTEGER NOT NULL,
    practical_max_marks INTEGER NOT NULL,
    theory_pass_marks INTEGER NOT NULL,
    practical_pass_marks INTEGER NOT NULL,
    grace_marks_allowed INTEGER NOT NULL DEFAULT 5,
    status VARCHAR(30) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'in_progress', 'completed', 'results_published')),
    workflow_instance_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, curriculum_id) REFERENCES curricula(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, course_id) REFERENCES courses(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, workflow_instance_id) REFERENCES workflow_instances(tenant_id, id) ON DELETE SET NULL
);
```

**RLS:** Enabled.

---

### 2. `exam_schedules`
**ADR:** ADR-043

```sql
CREATE TABLE exam_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    examination_id UUID NOT NULL,
    room_id UUID NOT NULL, -- FK to master_data_entities (room type)
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    invigilator_id UUID NOT NULL, -- FK to faculty
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, examination_id) REFERENCES examinations(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, invigilator_id) REFERENCES faculty(tenant_id, user_id) ON DELETE RESTRICT
);
```

**RLS:** Enabled.

---

### 3. `viva_scores`
**ADR:** ADR-038

```sql
CREATE TABLE viva_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    course_id UUID NOT NULL,
    professional_phase VARCHAR(30) NOT NULL,
    examiner_id UUID NOT NULL,
    marks_obtained NUMERIC(5, 2) NOT NULL,
    max_marks NUMERIC(5, 2) NOT NULL,
    conducted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, course_id) REFERENCES courses(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, examiner_id) REFERENCES faculty(tenant_id, user_id) ON DELETE RESTRICT
);
```

**RLS:** Enabled.

---

### 4. `practical_assessments`
**ADR:** ADR-038

```sql
CREATE TABLE practical_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    course_id UUID NOT NULL,
    professional_phase VARCHAR(30) NOT NULL,
    examiner_id UUID NOT NULL,
    marks_obtained NUMERIC(5, 2) NOT NULL,
    max_marks NUMERIC(5, 2) NOT NULL,
    conducted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, course_id) REFERENCES courses(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, examiner_id) REFERENCES faculty(tenant_id, user_id) ON DELETE RESTRICT
);
```

**RLS:** Enabled.

---

### 5. `clinical_evaluations`
**ADR:** ADR-038

```sql
CREATE TABLE clinical_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    course_id UUID NOT NULL,
    professional_phase VARCHAR(30) NOT NULL,
    evaluator_id UUID NOT NULL,
    marks_obtained NUMERIC(5, 2) NOT NULL,
    max_marks NUMERIC(5, 2) NOT NULL,
    posting_period VARCHAR(50) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, course_id) REFERENCES courses(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, evaluator_id) REFERENCES faculty(tenant_id, user_id) ON DELETE RESTRICT
);
```

**RLS:** Enabled.

---

### 6. `ia_aggregation`
**ADR:** ADR-038

```sql
CREATE TABLE ia_aggregation (
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    course_id UUID NOT NULL,
    professional_phase VARCHAR(30) NOT NULL,
    logbook_marks NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    viva_marks NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    practical_marks NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    clinical_marks NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    total_ia NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    ia_max NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    is_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, student_id, course_id, professional_phase),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, course_id) REFERENCES courses(tenant_id, id) ON DELETE RESTRICT
);
```

**RLS:** Enabled.

---

### 7. `exam_eligibility`
**ADR:** ADR-039

```sql
CREATE TABLE exam_eligibility (
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    examination_id UUID NOT NULL,
    is_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    blocking_reasons JSONB NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checked_by UUID NULL,
    PRIMARY KEY (tenant_id, student_id, examination_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, examination_id) REFERENCES examinations(tenant_id, id) ON DELETE CASCADE
);
```

**RLS:** Enabled.

---

### 8. `exam_results`
**ADR:** ADR-040, ADR-041, ADR-045

```sql
CREATE TABLE exam_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    examination_id UUID NOT NULL,
    theory_marks NUMERIC(5, 2) NULL,
    practical_marks NUMERIC(5, 2) NULL,
    ia_marks NUMERIC(5, 2) NULL,
    total_marks NUMERIC(5, 2) NULL,
    theory_grade VARCHAR(20) NULL,
    practical_grade VARCHAR(20) NULL,
    overall_grade VARCHAR(20) NULL,
    grace_marks_applied INTEGER NOT NULL DEFAULT 0,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(30) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'verified', 'approved', 'published')),
    workflow_instance_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, examination_id) REFERENCES examinations(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, workflow_instance_id) REFERENCES workflow_instances(tenant_id, id) ON DELETE SET NULL
);
```

**RLS:** Enabled.

---

### 9. `exam_moderation`
**ADR:** ADR-048

```sql
CREATE TABLE exam_moderation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    exam_result_id UUID NOT NULL,
    examiner_1_marks NUMERIC(5, 2) NOT NULL,
    examiner_2_marks NUMERIC(5, 2) NOT NULL,
    examiner_3_marks NUMERIC(5, 2) NULL,
    moderation_method VARCHAR(50) NOT NULL,
    final_marks NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, exam_result_id) REFERENCES exam_results(tenant_id, id) ON DELETE CASCADE
);
```

**RLS:** Enabled.

---

### 10. `mark_sheets`
**ADR:** ADR-042

```sql
CREATE TABLE mark_sheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    semester VARCHAR(20) NULL,
    pdf_asset_id UUID NOT NULL,
    qr_verification_code VARCHAR(100) NOT NULL UNIQUE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, pdf_asset_id) REFERENCES digital_assets(tenant_id, id) ON DELETE RESTRICT
);
```

**RLS:** Enabled.

---

### 11. `question_papers`
**ADR:** ADR-044

```sql
CREATE TABLE question_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    examination_id UUID NOT NULL,
    paper_type VARCHAR(30) NOT NULL CHECK (paper_type IN ('theory', 'practical', 'viva')),
    version INTEGER NOT NULL DEFAULT 1,
    asset_id UUID NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'approved', 'locked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, examination_id) REFERENCES examinations(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, asset_id) REFERENCES digital_assets(tenant_id, id) ON DELETE RESTRICT
);
```

**RLS:** Enabled.
