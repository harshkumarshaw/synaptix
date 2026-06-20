# NMC Compliance Tests — Synaptix

> **HARD-FAIL DOCUMENT.** Every regulation listed here MUST have a passing test in `tests/compliance/`. If any test fails, the build fails.
>
> Maintained by: NMC Compliance Agent
> Last updated: 2026-06-18

## Document Purpose

This file is the **regulation-to-test mapping**. Every NMC, GMER, AETCOM, Foundation Course, ECE, Electives, Logbook, and CBE regulation that Synaptix must enforce is listed here with its corresponding test.

When NMC publishes a circular or amendment, the NMC Compliance Agent updates this document FIRST (adds the new test requirement), THEN the Testing Agent implements the test, THEN the Backend Agent implements the code.

## Source Documents

- UG Curriculum Vol I, II, III (MCI/NMC CBME 2018)
- GMER 2019 Part II
- GMER 2023 / CBME Regulation 2023
- Foundation Course Module (2019)
- AETCOM Book (2018)
- Early Clinical Exposure Module (2019)
- Skills Training Module (2019)
- Electives Module (2020)
- Logbook Guidelines (2020)
- Assessment / CBA Module (2019)
- Alignment and Integration Module (2019)

---

## Part A: Attendance Regulations (CRITICAL)

### A.1 Two-Threshold Rule (GMER 2019 §11.1)

**Regulation text:** "A student shall not be permitted to appear in the University examinations of the Professional examination if his/her attendance is less than 75% in theory and 80% in practicals/clinicals."

**Tests required:**

| Test ID | Description | File |
|---------|-------------|------|
| ATT-NMC-001 | 75.00% theory → eligible | tests/compliance/attendance/test_thresholds.py |
| ATT-NMC-002 | 74.99% theory → blocked | tests/compliance/attendance/test_thresholds.py |
| ATT-NMC-003 | 80.00% practical → eligible | tests/compliance/attendance/test_thresholds.py |
| ATT-NMC-004 | 79.99% practical → blocked | tests/compliance/attendance/test_thresholds.py |
| ATT-NMC-005 | Theory pass + practical fail → split eligibility | tests/compliance/attendance/test_thresholds.py |
| ATT-NMC-006 | Theory fail + practical pass → split eligibility | tests/compliance/attendance/test_thresholds.py |

### A.2 Subject-Wise, Phase-Wise Enforcement

**Regulation:** Attendance must meet thresholds in EACH subject in EACH phase, not in aggregate.

**Tests required:**

| Test ID | Description |
|---------|-------------|
| ATT-NMC-021 | Student with 76% in Anatomy, 74% in Physiology: blocked from Physiology, eligible for Anatomy |
| ATT-NMC-022 | Multi-phase subject (Community Medicine): each phase tracked separately, aggregated for exam eligibility |
| ATT-NMC-023 | Attendance carries forward only within the same phase, not across phases |

### A.3 Elective Attendance (GMER 2019 §9.3.8)

**Regulation:** "75% attendance in each elective block is required for NExT eligibility."

| Test ID | Description |
|---------|-------------|
| ATT-NMC-011 | Elective Block 1: 75% threshold |
| ATT-NMC-012 | Elective Block 2: 75% threshold |
| ATT-NMC-024 | Block 1 and Block 2 tracked as separate pools |
| ATT-NMC-025 | Elective attendance does NOT compensate for regular attendance |

---

## Part B: Logbook Regulations

### B.1 Logbook Prerequisite (GMER §11.1.1.b.7)

**Regulation:** "The student shall be required to maintain a logbook... Submission of completed logbook shall be a prerequisite for appearing in the final summative examination."

| Test ID | Description |
|---------|-------------|
| LOG-NMC-012 | Logbook NOT submitted → hall ticket blocked |
| LOG-NMC-015 | Logbook submitted but NOT assessed → hall ticket blocked |
| LOG-NMC-016 | Logbook submitted AND assessed → eligible (if other conditions met) |

### B.2 Logbook IA Contribution

**Regulation:** "Up to 20% of IA marks shall come from logbook assessment."

| Test ID | Description |
|---------|-------------|
| LOG-NMC-013 | 20% IA contribution applied when logbook complete |
| LOG-NMC-014 | 0% IA contribution when logbook incomplete |
| LOG-NMC-017 | IA weight configurable per institution (0-20% range) |

### B.3 Logbook Scope (Full)

**Regulation:** Logbook covers ALL subjects, ALL phases, plus Foundation Course, AETCOM, ECE, electives.

| Test ID | Description |
|---------|-------------|
| LOG-NMC-001 | Logbook has section for every subject in current phase |
| LOG-NMC-002 | Logbook has Foundation Course section (Phase I only) |
| LOG-NMC-003 | Logbook has AETCOM section per phase |
| LOG-NMC-004 | Logbook has ECE section (Phase I) |
| LOG-NMC-005 | Logbook has Elective Block 1 and Block 2 sections (Phase III Part I) |

### B.4 Logbook Entry Fields

**Regulation:** Each entry must contain specific fields per Logbook Guidelines 2020.

| Test ID | Description |
|---------|-------------|
| LOG-NMC-006 | Entry contains competency_code |
| LOG-NMC-007 | Entry contains nmc_level (K/KH/SH/P) |
| LOG-NMC-008 | Entry contains is_core (Y/N) |
| LOG-NMC-009 | Entry contains faculty_initials and faculty_date |
| LOG-NMC-010 | Entry contains student_initials |
| LOG-NMC-011 | Entry contains attempt_type (F/R/Re), rating (B/M/E), faculty_decision (C/R/Re) |

---

## Part C: Foundation Course (GMER 2019, Module 1)

### C.1 Foundation Course Mandate

**Regulation:** "A Foundation Course of 1 month duration shall be conducted at the commencement of Phase I."

| Test ID | Description |
|---------|-------------|
| FC-NMC-001 | Foundation Course scheduled as 1-month block at Phase I start |
| FC-NMC-002 | Foundation Course components: orientation, BLS, communication, computer/library, professional values, sports/yoga, hospital/village/PHC visits, SDL intro, AETCOM intro |
| FC-NMC-003 | Foundation Course attendance tracked separately |
| FC-NMC-004 | Foundation Course completion certificate generated on satisfactory completion |

---

## Part D: AETCOM (AETCOM Book 2018)

### D.1 AETCOM Longitudinal

**Regulation:** AETCOM runs across Phase I, II, III Part I, III Part II with its own competency list per year.

| Test ID | Description |
|---------|-------------|
| AET-NMC-001 | AETCOM session event type supported |
| AET-NMC-002 | AETCOM competency codes (ATT-X, ETH-X, COM-X) in Competency Bank |
| AET-NMC-003 | AETCOM logbook entries with student reflection + faculty feedback |
| AET-NMC-004 | AETCOM IA: written + OSCE/viva components |
| AET-NMC-005 | AETCOM completion required per phase before progression |

---

## Part E: Early Clinical Exposure (ECE Module 2019)

### E.1 ECE in Phase I

**Regulation:** ECE introduced in Phase I to contextualise basic sciences.

| Test ID | Description |
|---------|-------------|
| ECE-NMC-001 | ECE event type allowed only in Phase I |
| ECE-NMC-002 | Clinical postings event type NOT allowed in Phase I |
| ECE-NMC-003 | ECE attendance counts toward practical pool (80%) |
| ECE-NMC-004 | ECE logbook entries supported |

---

## Part F: Electives (Electives Module 2020, GMER 2019 §9.3)

### F.1 Elective Structure

**Regulation:** 2 months total = Block 1 (4 weeks) + Block 2 (4 weeks). Scheduled after Phase III Part I exam.

| Test ID | Description |
|---------|-------------|
| EL-NMC-001 | Electives configured as 2-month block after Phase III Part I exam |
| EL-NMC-002 | Block 1: pre-clinical/para-clinical OR research project |
| EL-NMC-003 | Block 2: clinical department OR community clinic |
| EL-NMC-004 | Elective allocation workflow: students rank, system allocates |
| EL-NMC-005 | Supervisor assignment per student per block |
| EL-NMC-006 | Elective 75% attendance enforced |
| EL-NMC-007 | Elective logbook required for both blocks |
| EL-NMC-008 | Elective completion = 75% attendance + logbook + supervisor sign-off |
| EL-NMC-009 | Electives cannot compensate for regular attendance |
| EL-NMC-010 | Elective completion required for NExT eligibility |

---

## Part G: Skills Lab & DOAP (Skills Training Module 2019)

### G.1 DOAP Methodology

**Regulation:** Skills acquired via Demonstration → Observation → Assistance → Performance.

| Test ID | Description |
|---------|-------------|
| DOAP-NMC-001 | DOAP session event type supported |
| DOAP-NMC-002 | Stage tracked: D/O/A/P |
| DOAP-NMC-003 | Rating tracked: B/M/E or numerical |
| DOAP-NMC-004 | Attempt type tracked: F/R/Re |
| DOAP-NMC-005 | Faculty decision tracked: C/R/Re |
| DOAP-NMC-006 | Certifiable competencies (P level) signed off before graduation |
| DOAP-NMC-007 | Certified skills feed NExT eligibility check |

---

## Part H: Competency Taxonomy (NMC CBME)

### H.1 K/KH/SH/P Levels

**Regulation:** Miller's pyramid adapted: Knows, Knows How, Shows How, Performs.

| Test ID | Description |
|---------|-------------|
| CBE-NMC-001 | Competency table stores nmc_level (K/KH/SH/P) |
| CBE-NMC-002 | Competency level can ascend across phases (K in P1 → P in internship) |
| CBE-NMC-003 | Core/non-core designation tracked (is_core Y/N) |
| CBE-NMC-004 | All core competencies must be achieved for graduation |
| CBE-NMC-005 | Non-core competencies optional |
| CBE-NMC-006 | Phase I competency cannot be signed off at P level (must be K or KH) |
| CBE-NMC-007 | Competency code uniqueness scoped to curriculum_id |

---

## Part I: Examination Framework

### I.1 IA Components

**Regulation:** IA includes theory written, practical, OSPE, OSCE, DOPS, mini-CEX, end-of-posting, logbook, AETCOM IA.

| Test ID | Description |
|---------|-------------|
| EXM-NMC-021 | Assessment type IA_Theory_Written supported |
| EXM-NMC-022 | Assessment type IA_Practical supported |
| EXM-NMC-023 | Assessment type IA_OSPE supported (pre/para-clinical) |
| EXM-NMC-024 | Assessment type IA_OSCE supported (clinical) |
| EXM-NMC-025 | Assessment type IA_DOPS supported |
| EXM-NMC-026 | Assessment type IA_miniCEX supported |
| EXM-NMC-027 | Assessment type IA_EndPosting supported |
| EXM-NMC-028 | Assessment type IA_Logbook supported |
| EXM-NMC-029 | Assessment type IA_AETCOM_Written supported |
| EXM-NMC-030 | Assessment type IA_AETCOM_OSCE supported |

### I.2 NExT Exam (CBME 2023)

| Test ID | Description |
|---------|-------------|
| EXM-NMC-011 | NExT eligibility additionally requires elective logbooks |
| EXM-NMC-031 | NExT Step 1 and Step 2 configured as assessment types |
| EXM-NMC-032 | NExT eligibility checks ALL prerequisites in one operation |

---

## Part J: CRMI (Compulsory Rotating Medical Internship)

### J.1 Mandatory Rotations

| Test ID | Description |
|---------|-------------|
| CRMI-NMC-001 | 7 mandatory rotations enforced |
| CRMI-NMC-002 | General Medicine: 2 months (with Psychiatry OR TB&Resp 15 days) |
| CRMI-NMC-003 | General Surgery: 2 months (with Ortho 15 days) |
| CRMI-NMC-004 | OBG: 2 months |
| CRMI-NMC-005 | Paediatrics: 1 month |
| CRMI-NMC-006 | Community Medicine: 2 months (incl. rural) |
| CRMI-NMC-007 | Emergency/Casualty: 1 month |
| CRMI-NMC-008 | Elective: 15 days from approved list |

### J.2 CRMI Rules

| Test ID | Description |
|---------|-------------|
| CRMI-NMC-009 | 75% attendance PER ROTATION (not aggregate) |
| CRMI-NMC-010 | Max 15 days leave for ENTIRE CRMI |
| CRMI-NMC-011 | Intern at 15 days leave: leave application blocked |
| CRMI-NMC-012 | Intern at 12 days leave: early warning |
| CRMI-NMC-013 | Rotation extension on attendance shortfall: extends to reach 75% |
| CRMI-NMC-015 | Leave cap does not reset after extension |
| CRMI-NMC-016 | CRMI Completion Certificate requires ALL rotations satisfactory |
| CRMI-NMC-019 | Only ONE active CRMI enrollment per student |

---

## Part K: Curriculum Committee & MEU

### K.1 Mandatory Bodies

**Regulation:** Every medical college must have a functional Curriculum Committee and MEU.

| Test ID | Description |
|---------|-------------|
| CC-NMC-001 | Curriculum Committee role in RBAC |
| CC-NMC-002 | MEU faculty role in RBAC |
| CC-NMC-003 | Curriculum Committee meeting records maintained |
| CC-NMC-004 | MEU faculty development programmes tracked |

---

## Part L: Family Adoption Programme

### L.1 Curricular Activity

**Regulation:** Family Adoption Programme mandatory in Phase I, linked to Community Medicine.

| Test ID | Description |
|---------|-------------|
| FAP-NMC-001 | Family/village assignment per batch |
| FAP-NMC-002 | Visit schedule and attendance tracked |
| FAP-NMC-003 | Attendance counts as official duty |
| FAP-NMC-004 | Visit records linked to Community Medicine completion |

---

## Part M: Hall Ticket / NExT Eligibility Flow

### M.1 Eligibility Pipeline

| Test ID | Description |
|---------|-------------|
| ELG-NMC-001 | Theory ≥75% per subject |
| ELG-NMC-002 | Practical ≥80% per subject |
| ELG-NMC-003 | Logbook submitted AND assessed per phase |
| ELG-NMC-004 | IA min tests completed per subject |
| ELG-NMC-005 | AETCOM IA completed per phase |
| ELG-NMC-006 | Certifiable competencies signed off |
| ELG-NMC-007 | Fee clearance |
| ELG-NMC-008 | NExT additionally: elective Block 1 logbook submitted |
| ELG-NMC-009 | NExT additionally: elective Block 2 logbook submitted |
| ELG-NMC-010 | NExT additionally: elective attendance ≥75% (both blocks) |
| ELG-NMC-011 | All checks pass: hall ticket auto-generated |
| ELG-NMC-012 | Any check fails: flagged for Principal review |
| ELG-NMC-013 | Principal exemption: audit-logged with reason |

---

## Updating This Document

When a new NMC circular is published or a regulation interpretation changes:

1. NMC Compliance Agent reads the new regulation
2. Adds test entries to this file with `[PROPOSED]` prefix
3. Human supervisor reviews and approves
4. Removes `[PROPOSED]` prefix
5. Testing Agent implements the tests
6. Backend Agent implements the enforcement
7. Update `docs/NMC_COMPLIANCE_LOG.md` with the regulation → module → test mapping

---

*Source of truth for NMC compliance. Hard-fail enforcement. No exceptions.*
