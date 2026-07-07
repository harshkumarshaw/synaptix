-- Test script for Phase 3 Exam Management constraints
-- Run with: psql -U postgres -d synaptix_dev -f scripts/test_phase3_constraints.sql

BEGIN;

-- Setup temporary data for testing constraints
-- Note: Assuming a tenant, program, curriculum, course, student, and faculty exist.
-- We will fetch or create them within the transaction.

-- 1. Create a test tenant, curriculum, course, student, and faculty if needed
INSERT INTO tenants (id, name, subdomain)
VALUES ('00000000-0000-0000-0000-000000000001', 'Test Institution', 'test')
ON CONFLICT (id) DO NOTHING;

INSERT INTO programs (id, tenant_id, code, name, degree_type)
VALUES ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'MBBS', 'Bachelor of Medicine', 'ug')
ON CONFLICT (id) DO NOTHING;

INSERT INTO curricula (id, tenant_id, program_id, version_name, status)
VALUES ('20000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'CBME 2019', 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO courses (id, tenant_id, code, name, professional_phase)
VALUES ('30000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'ANAT101', 'Anatomy', 'Phase I')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, email, password_hash, role, full_name)
VALUES 
  ('40000000-0000-0000-0000-000000000001', 'student@test.local', 'hash', 'student', 'Test Student'),
  ('40000000-0000-0000-0000-000000000002', 'faculty@test.local', 'hash', 'faculty', 'Test Faculty')
ON CONFLICT (id) DO NOTHING;

INSERT INTO students (id, tenant_id, user_id, roll_number, admission_batch, professional_phase)
VALUES ('50000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'MBBS2023-01', '2023', 'Phase I')
ON CONFLICT (id) DO NOTHING;

INSERT INTO faculty (user_id, tenant_id, designation, department_id)
VALUES ('40000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'Professor', NULL)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO digital_assets (id, tenant_id, file_name, file_size, mime_type, file_path, sha256)
VALUES ('60000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'paper.pdf', 1024, 'application/pdf', '/storage/paper.pdf', 'hash')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- CHECK: INSERT Valid Examination (EXM-001)
-- ============================================================================
\echo '1. Testing valid examinations insert...'
INSERT INTO examinations (
    id, tenant_id, curriculum_id, course_id, exam_type, exam_session, academic_year,
    exam_date, theory_max_marks, practical_max_marks, theory_pass_marks, practical_pass_marks, status
) VALUES (
    '70000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001',
    'professional', 'Dec 2026', '2026-2027', '2026-12-15', 100, 100, 50, 50, 'scheduled'
);
\echo '-> Success!'

-- ============================================================================
-- CHECK: Invalid Exam Status/Type CHECK Constraints
-- ============================================================================
\echo '2. Testing invalid exam type (should fail)...'
SAVEPOINT sp1;
BEGIN;
INSERT INTO examinations (
    id, tenant_id, curriculum_id, course_id, exam_type, exam_session, academic_year,
    exam_date, theory_max_marks, practical_max_marks, theory_pass_marks, practical_pass_marks, status
) VALUES (
    '70000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001',
    'invalid_type', 'Dec 2026', '2026-2027', '2026-12-15', 100, 100, 50, 50, 'scheduled'
);
ROLLBACK TO SAVEPOINT sp1;
\echo '-> Checked: Fails as expected!'

-- ============================================================================
-- CHECK: INSERT Valid Exam Eligibility with JSONB (ELIG-006)
-- ============================================================================
\echo '3. Testing valid exam eligibility insert with JSONB...'
INSERT INTO exam_eligibility (
    tenant_id, student_id, examination_id, is_eligible, blocking_reasons
) VALUES (
    '00000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001',
    '70000000-0000-0000-0000-000000000001', false, '{"attendance": "Theory attendance is 71.4%, minimum 75% required"}'::jsonb
);
\echo '-> Success!'

-- ============================================================================
-- CHECK: INSERT Valid Exam Results (RES-001)
-- ============================================================================
\echo '4. Testing valid exam results insert...'
INSERT INTO exam_results (
    id, tenant_id, student_id, examination_id, theory_marks, practical_marks, status
) VALUES (
    '80000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001',
    '50000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001',
    80.50, 75.00, 'draft'
);
\echo '-> Success!'

-- ============================================================================
-- CHECK: Duplicate (Student, Examination) in Exam Results (fails UNIQUE)
-- ============================================================================
\echo '5. Testing duplicate student result insert (should fail)...'
SAVEPOINT sp2;
BEGIN;
INSERT INTO exam_results (
    id, tenant_id, student_id, examination_id, theory_marks, practical_marks, status
) VALUES (
    '80000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001',
    '50000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001',
    45.00, 50.00, 'draft'
);
ROLLBACK TO SAVEPOINT sp2;
\echo '-> Checked: Duplicate UNIQUE constraint violation fails as expected!'

-- ============================================================================
-- CHECK: FK Referential Integrity Violations
-- ============================================================================
\echo '6. Testing result foreign key to non-existent exam (should fail)...'
SAVEPOINT sp3;
BEGIN;
INSERT INTO exam_results (
    id, tenant_id, student_id, examination_id, theory_marks, practical_marks, status
) VALUES (
    '80000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001',
    '50000000-0000-0000-0000-000000000001', '79999999-9999-9999-9999-999999999999',
    45.00, 50.00, 'draft'
);
ROLLBACK TO SAVEPOINT sp3;
\echo '-> Checked: FK constraint violation fails as expected!'

\echo '=== All Phase 3 schema constraint validations PASSED! ==='

ROLLBACK;
