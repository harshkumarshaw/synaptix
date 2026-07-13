# HANDOFF_NOTES.md

## Current State
- **Session 26 (2026-07-11):** Phase 3 R4.3 and R4.4 exam service result processing, grading, moderation, and mark sheet PDF generation are fully implemented and verified. All 50 unit and compliance tests are 100% green. 
- Integrated WeasyPrint and qrcode packages for official mark sheet generation.
- Corrected audit logging action constraint issues by converting all action names to uppercase (e.g. `SUBMIT_RESULT`, `GENERATE_MARK_SHEET`).

## Key Schema Knowledge
- `courses.code` = unique suffixed code (e.g. `ANAT_ee68c1`). NEVER use for logbook/prerequisite lookups.
- `courses.subject_code` = canonical subject abbreviation (e.g. `ANAT`). USE THIS for service logic.
- `clinical_evaluations.evaluator_id → faculty(tenant_id, user_id)` — pass `user_id`, NOT `faculty.id`.
- `practical_assessments.examiner_id → faculty(tenant_id, user_id)` — same rule.
- `viva_scores.examiner_id → faculty(tenant_id, user_id)` — same rule.
- `audit_log.action` enforces strict uppercase format `chk_audit_log_action CHECK (action ~ '^[A-Z_]+$')`.

## Tasks Pending — Explicit Recipients

### [TO: Frontend Agent]
- Build frontend UI components for Phase B-D Electives & Leave UI (F4 plan).
- Add Playwright E2E tests for any new frontend pages built.
- Ensure the existing E2E test suite remains green.

## Debt List — Honest Assessment
- All 8 unit tests in `test_grading.py` are fully passing (no xfail).
- 50/50 backend tests are green.
- No remaining debt from Phase 3 R4.
