# Phase 3 Test Categorisation & Deferral List

**Status:** Draft — R0 baseline (Examination Management)
**Created:** 2026-07-04 (Session 19)
**Last updated:** 2026-07-04

This document defines the categorization of all Phase 3 test cases, specifying which tests are mandatory for the Phase 3 MVP, which are deferred to Phase 3.5, and which are deferred to Phase 4.

---

## 1. Must Pass Phase 3 (MVP) — 43 Tests

These tests represent the core scheduling, internal assessment aggregation, eligibility check, grade calculations, and results publication workflows.

### Examination Scheduling & Lifecycle
- `EXM-011`: Exam scheduling: room availability check
- `EXM-012`: Exam scheduling: invigilator clash check
- `EXM-013`: Exam scheduling: student clash check
- `EXM-014`: Exam lifecycle: transitions from scheduled to results_published
- `EXM-015`: Question paper workflow: upload by setter, lock by controller
- `EXM-019`: Cancel exam schedule releases room and notifies candidates
- `EXM-020`: Reschedule exam date updates calendars and checks for new conflicts

### IA Aggregation
- `IA-001`: Logbook completion IA contribution (up to 20%)
- `IA-002`: Viva scores IA contribution (30%)
- `IA-003`: Practical exam scores IA contribution (30%)
- `IA-004`: Clinical posting evaluation IA contribution (20%)
- `IA-005`: MDM configuration of subject-specific weights
- `IA-006`: Capping total IA contribution at 20% validation
- `IA-007`: Aggregate IA calculations for whole batch
- `IA-008`: Missing sub-component marks treated as zero in aggregation
- `IA-010`: Historical IA records retained on re-calculation

### Exam Eligibility Engine
- `ELIG-001`: Eligibility check: attendance requirements met
- `ELIG-002`: Eligibility check: certified logbooks
- `ELIG-003`: Eligibility check: aggregate IA marks >= 50%
- `ELIG-004`: Eligibility check: no active disciplinary suspension
- `ELIG-005`: Eligibility check: prerequisite courses passed
- `ELIG-006`: Eligibility returns detailed blocking reasons on failure
- `ELIG-007`: Eligibility batch run returns list of eligible student IDs
- `ELIG-008`: Principal overrides exam eligibility with audit log
- `ELIG-009`: Dean overrides exam eligibility with audit log
- `ELIG-010`: Cross-tenant student eligibility isolation

### Grading & Supplementary
- `RES-001`: Grading: Distinction (>=75%) calculation
- `RES-002`: Grading: Pass (50%-74%) calculation
- `RES-003`: Grading: Fail (<50%) calculation
- `RES-004`: Theory and practical parts evaluated and passed independently
- `RES-005`: Multi-examiner moderation: average of two if <=15% diff
- `RES-006`: Multi-examiner moderation: third examiner if >15% diff
- `RES-007`: Supplementary exam: attempts count limited to 4 (NMC Regulation)
- `RES-008`: Supplementary exam: grace marks not allowed
- `RES-009`: Grace marks policy: up to 5 marks applied automatically
- `RES-010`: Result publication workflow transitions

### Mark Sheets & Verification
- `MKS-001`: Mark sheet PDF generation using WeasyPrint
- `MKS-002`: QR verification code embedded and verified
- `MKS-003`: Mark sheet stored as digital asset

---

## 2. Deferred to Phase 3.5 — 4 Tests

These tests represent advanced security, logging, or non-blocking validations.

- `EXM-016`: Question paper access control: only exam controller can view before exam date (Deferred due to advanced security key-management requirement)
- `EXM-017`: Invigilator assignment audit logs (Deferred to align with log aggregation updates)
- `EXM-018`: Room capacity warning threshold check during scheduling (Non-blocking warning)
- `IA-009`: Audit log entry created on IA configuration change (Audit trail extensions)

---

## 3. Deferred to Phase 4 — 2 Tests

These tests represent complex integrations or external system signatures.

- `MKS-004`: Digital signature placeholder rendered (Requires certificate authority integration)
- `MKS-005`: University bulk mark sheet generation idempotency (Requires university API integrations)
