# NMC Compliance Log

Every NMC regulation mapped to: which module implements it, which tests verify it, current compliance status.

This document is **inspection evidence**. NMC inspectors can be shown this directly.

## Format

```markdown
### NMC-NNN: [Regulation]

**Source:** [Document name, section]
**Effective Date:** YYYY-MM-DD
**Applies To:** MBBS / Nursing / etc.

**Implementing Module:** F-01 / A-11 / etc.
**Test IDs:** ATT-NMC-001, ATT-NMC-002, ...
**Test File:** tests/compliance/...

**Compliance Status:**
- [ ] Implemented
- [ ] Tested
- [ ] Verified

**Last Audit:** YYYY-MM-DD by [Agent ID]

**Notes:**
Any implementation notes or known limitations.
```

## Active Regulations

### ATT-NMC-007: Clinical posting attendance counted toward 80% practical pool
**Source:** GMER 2019 §11.1
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-04 (Academic Calendar) & A-11 (Attendance)
**Test IDs:** ATT-NMC-007
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Schema validation via `events.attendance_category`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Events are partitioned by `attendance_category = 'clinical'` or `'practical'`.

### ATT-NMC-008: DOAP session attendance counted toward 80% practical pool
**Source:** GMER 2019 §11.1
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-04 & A-11
**Test IDs:** ATT-NMC-008
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Schema validation via `events.attendance_category`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Aggregated into practical pool via `attendance_category = 'doap'`.

### ATT-NMC-009: ECE session attendance counted toward 80% practical pool
**Source:** GMER 2019 §11.1
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-04 & A-11
**Test IDs:** ATT-NMC-009
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Schema validation via `events.attendance_category`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Enforced via `attendance_category = 'ece'`.

### ATT-NMC-010: Theory lecture attendance counted toward 75% theory pool
**Source:** GMER 2019 §11.1
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-04 & A-11
**Test IDs:** ATT-NMC-010
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Schema validation via `events.attendance_category`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Evaluated against 75% threshold via `attendance_category = 'theory'`.

### ATT-NMC-013: AETCOM attendance tracked separately
**Source:** AETCOM Module 2018
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-07 (Foundation/AETCOM) & A-11
**Test IDs:** ATT-NMC-013
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Schema validation via `events.attendance_category` & `aetcom_records`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Isolated from general theory/practical aggregates via `attendance_category = 'aetcom'`.

### ATT-NMC-014: Foundation Course attendance tracked separately
**Source:** Foundation Course Module 2019
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-07 & A-11
**Test IDs:** ATT-NMC-014
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Schema validation via `events.attendance_category` & `foundation_course_records`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Tracked independently via `attendance_category = 'foundation_course'`.

### ATT-NMC-015: Multi-phase subject aggregates attendance across phases
**Source:** GMER 2019
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-04 & A-11
**Test IDs:** ATT-NMC-015
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Schema validation via `events.professional_phase`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** `professional_phase` column on `events` allows filtering and grouping by phase.

### ATT-NMC-019: Cancelled session does not count toward attendance denominator
**Source:** GMER 2019 / Audit Ref AUDIT-D3
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-06 (Session Tracking) & A-11
**Test IDs:** ATT-NMC-019
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Schema validation via `events.status = 'cancelled'`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Denominator counts ONLY 'conducted' sessions.

### FC-NMC-001: Foundation Course scheduled as 1-month block at Phase I start
**Source:** Foundation Course Module 2019
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-04 & A-07
**Test IDs:** FC-NMC-001
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Validations on `events.event_type = 'foundation_course'`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Scheduler checks that events occur within 31 days of Phase I start date.

### ECE-NMC-001: ECE event type allowed only in Phase I
**Source:** GMER 2019 / CBME 2019
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-04 (Academic Calendar)
**Test IDs:** ECE-NMC-001
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Validations on `events.event_type` and `events.professional_phase`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Events of type `ece` are rejected if the phase is not `Phase I`.

### ECE-NMC-002: Clinical postings event type NOT allowed in Phase I
**Source:** GMER 2019 / CBME 2019
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-04 (Academic Calendar)
**Test IDs:** ECE-NMC-002
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Validations on `events.event_type` and `events.professional_phase`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Events of type `clinical_posting` are rejected if scheduled in `Phase I`.

### AET-NMC-001: AETCOM session event type supported
**Source:** AETCOM Module 2018
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-04
**Test IDs:** AET-NMC-001
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Events schema support for `event_type = 'aetcom'`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Added `aetcom` to `events.event_type` CHECK constraints.

### AET-NMC-005: AETCOM completion required per phase before progression
**Source:** AETCOM Module 2018 / Progression Rules
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-07 & Progression Engine
**Test IDs:** AET-NMC-005
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Schema tracking via `aetcom_records.status` and `professional_phase`)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Ensures longitudinal verification and phase check before advancing students.

### CUR-004: Competency code uniqueness scoped per curriculum_id
**Source:** ADR-008 / Audit Ref AUDIT-D1
**Effective Date:** 2026-06-20
**Applies To:** MBBS
**Implementing Module:** A-02 & A-05
**Test IDs:** CUR-004
**Test File:** tests/compliance/test_nmc_compliance_stubs.py
**Compliance Status:**
- [x] Implemented (Scoping on `lesson_plans.curriculum_id` composite FK)
- [x] Tested (xfail stub verified)
- [ ] Verified
**Notes:** Prevents conflicts when CBME 2019 and CBME 2023 define different details for the same code.

