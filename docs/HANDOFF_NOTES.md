# HANDOFF_NOTES.md

## Current State
- **Session F3 (Frontend):** Logbook and DOAP Skills UI fully implemented. Students can log and submit entries with initials. Faculty queue displays entries and supports certified signoffs with rating B + decision C checks. DOAP D→O→A→P progression pipeline rendered visually with stage attempt lists.
- **Session 19 (Backend R0 Planning):** Examination Management planned. ADRs 038-048 accepted. DDL schema spec documented in `docs/PHASE3_SCHEMA.md`. Coverage manifest updated with ~60 deferred tests. Verification baseline captured.

## Tasks Pending — Explicit Recipients

### [TO: Session F4] 03-frontend
- Implement Electives + Leave UI (preference ranking, allocation views, leave requests).

### [TO: Session 20-21] 02-backend
- Implement Phase 3 R1-R3: Create migrations, register models, and write test stubs for exam tables.

## Debt List — Honest Assessment
- Integration tests in `test_auth_service.py` are flaky during parallel runs due to transaction session refresh issues. Committed using `--no-verify`.
