# Phase 2 Test Categorisation

**Date:** 2026-07-01
**Created by:** Orchestrator Agent (00), Session 11
**Baseline verifier run:** docs/verification/baseline_coverage_20260701.txt

> All test descriptions are taken verbatim from the `description:` field in `tests/COVERAGE_MANIFEST.yaml`.
> No descriptions are sourced from the Phase 2 Complete Plan or other documents.
> Each deferred ID includes the actual description for human verification.

---

## Summary

| Category | Count |
|----------|-------|
| Already passing (in codebase) | 20 |
| Must pass in Phase 2 (missing or xfail) | 98 |
| Deferred to Phase 2.5 (hardware/mobile) | 21 |
| Deferred to Phase 3+ | 100 |
| **Total in manifest** | **239** |

---

## Categorisation Rules Applied

- **Must pass Phase 2:** Feature is implemented or should be implemented before Phase 2 completion. Test must pass.
- **Phase 2.5:** Offline mobile sync, RFID hardware, GPS geofencing, biometric integration — hardware/mobile dependencies that cannot be tested without physical devices or mobile app.
- **Phase 3+:** Face recognition, full examination management, full CRMI/internship module, curriculum migration engine, full auth integration — features not scoped for Phase 2.
- **Default rule:** When in doubt, categorise as "Must pass Phase 2." Stricter is safer.

---

## Full Categorisation Table

### FOUNDATION LAYER (F-series)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| AUTH-001 | User with valid credentials can log in | identity_access_management | missing | Yes | — | — |
| AUTH-002 | User with invalid password cannot log in | identity_access_management | missing | Yes | — | — |
| AUTH-003 | JWT token contains user_id, tenant_id, roles, exp | identity_access_management | missing | Yes | — | — |
| AUTH-004 | Expired JWT is rejected | identity_access_management | missing | Yes | — | — |
| AUTH-005 | MFA is enforced for admin role | identity_access_management | missing | No | Phase 3 | Full MFA integration requires mobile authenticator app |
| AUTH-006 | MFA is enforced for principal role | identity_access_management | missing | No | Phase 3 | Full MFA integration requires mobile authenticator app |
| AUTH-007 | MFA is enforced for dean role | identity_access_management | missing | No | Phase 3 | Full MFA integration requires mobile authenticator app |
| AUTH-008 | MFA is enforced for controller_of_examinations role | identity_access_management | missing | No | Phase 3 | Full MFA integration requires mobile authenticator app |
| AUTH-009 | MFA is NOT enforced for student role | identity_access_management | missing | Yes | — | — |
| AUTH-010 | MFA is NOT enforced for faculty role | identity_access_management | missing | Yes | — | — |
| AUTH-011 | Refresh token rotation works correctly | identity_access_management | missing | Yes | — | — |
| AUTH-012 | Concurrent sessions for same user are allowed | identity_access_management | missing | Yes | — | — |
| AUTH-013 | Account locks after 5 failed login attempts | identity_access_management | missing | Yes | — | — |
| AUTH-014 | Account unlocks after configured cooldown | identity_access_management | missing | Yes | — | — |
| AUTH-015 | Password reset via email OTP works | identity_access_management | missing | Yes | — | — |
| AUTH-016 | OTP login for students without institutional email works | identity_access_management | missing | Yes | — | — |
| AUTH-017 | Cross-tenant token usage is rejected | identity_access_management | missing | Yes | — | — |
| AUTH-018 | Audit log entry created on every login attempt | identity_access_management | missing | Yes | — | — |
| AUTH-019 | Audit log entry created on every permission grant/revoke | identity_access_management | missing | Yes | — | — |
| AUTH-020 | Session invalidation on password change | identity_access_management | missing | Yes | — | — |
| AUTH-E001 | User exists in two tenants (cross-tenant faculty) — separate sessions per tenant | identity_access_management | missing | Yes | — | — |
| AUTH-E002 | User with deactivated tenant cannot log in | identity_access_management | missing | Yes | — | — |
| AUTH-E003 | User logged in while their account is deactivated mid-session | identity_access_management | missing | Yes | — | — |
| AUTH-E004 | JWT secret rotation — old tokens invalidated, new ones work | identity_access_management | missing | Yes | — | — |
| AUTH-E005 | Inspector account auto-deactivates after expiry | identity_access_management | missing | Yes | — | — |
| MDM-001 | Create master data entity (department) | master_data_management | missing | Yes | — | — |
| MDM-002 | Update master data entity preserves history | master_data_management | missing | Yes | — | — |
| MDM-003 | Soft delete master data entity | master_data_management | missing | Yes | — | — |
| MDM-004 | Cannot delete entity if referenced by other records | master_data_management | missing | Yes | — | — |
| MDM-005 | Tenant onboarding seeds medical college template correctly | master_data_management | missing | Yes | — | — |
| MDM-006 | Tenant onboarding seeds nursing college template correctly | master_data_management | missing | Yes | — | — |
| MDM-007 | Bulk import via CSV validates and reports errors | master_data_management | missing | Yes | — | — |
| MDM-008 | Master data is tenant-scoped (cross-tenant invisible) | master_data_management | missing | Yes | — | — |
| WFL-001 | Create workflow definition with step JSON validation | workflow_engine | missing | Yes | — | — |
| WFL-002 | Immutability of workflow definitions on update (creates new version) | workflow_engine | missing | Yes | — | — |
| WFL-003 | Only one version of workflow definition is current | workflow_engine | missing | Yes | — | — |
| WFL-004 | Create workflow instance with static context snapshot | workflow_engine | missing | Yes | — | — |
| WFL-005 | Workflow instance transition appends to transitions table and history JSONB trigger | workflow_engine | missing | Yes | — | — |
| WFL-006 | Workflow instance respects composite FK tenant isolation | workflow_engine | missing | Yes | — | — |
| WFL-007 | Prevent duplicate active instances for a single entity | workflow_engine | missing | Yes | — | — |
| WFL-008 | Soft-deleted assignee handler delegates or escalates | workflow_engine | missing | Yes | — | — |
| AST-001 | Upload digital asset computes sha256 checksum and saves metadata | digital_assets | missing | Yes | — | — |
| AST-002 | Asset storage operates through abstract StorageProvider interface | digital_assets | missing | Yes | — | — |
| AST-003 | Write log to asset_download_log on file access | digital_assets | missing | Yes | — | — |
| AST-004 | Asset upload supports files larger than 2.1GB (BIGINT) | digital_assets | missing | Yes | — | — |

### ATTENDANCE ENGINE (A-11)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| ATT-NMC-001 | Student with EXACTLY 75.00% theory attendance is ELIGIBLE for theory exam | attendance_engine | missing | Yes | — | NMC GMER 2019 §11.1 — hard compliance |
| ATT-NMC-002 | Student with 74.99% theory attendance is BLOCKED for theory exam | attendance_engine | missing | Yes | — | NMC GMER 2019 §11.1 — hard compliance |
| ATT-NMC-003 | Student with EXACTLY 80.00% practical attendance is ELIGIBLE for practical exam | attendance_engine | missing | Yes | — | NMC GMER 2019 §11.1 — hard compliance |
| ATT-NMC-004 | Student with 79.99% practical attendance is BLOCKED for practical exam | attendance_engine | missing | Yes | — | NMC GMER 2019 §11.1 — hard compliance |
| ATT-NMC-005 | Student with 76% theory AND 79% practical: theory eligible, practical blocked | attendance_engine | missing | Yes | — | NMC GMER 2019 §11.1 — hard compliance |
| ATT-NMC-006 | Student with 74% theory AND 81% practical: theory blocked, practical eligible | attendance_engine | missing | Yes | — | NMC GMER 2019 §11.1 — hard compliance |
| ATT-NMC-007 | Clinical posting attendance counted toward 80% practical pool, not 75% theory | attendance_engine | missing | Yes | — | — |
| ATT-NMC-008 | DOAP session attendance counted toward 80% practical pool | attendance_engine | missing | Yes | — | — |
| ATT-NMC-009 | ECE session attendance counted toward 80% practical pool | attendance_engine | missing | Yes | — | — |
| ATT-NMC-010 | Theory lecture attendance counted toward 75% theory pool | attendance_engine | missing | Yes | — | — |
| ATT-NMC-011 | Elective Block 1 attendance threshold is 75% (separate pool) | attendance_engine | missing | Yes | — | NMC GMER 2019 §9.3 |
| ATT-NMC-012 | Elective Block 2 attendance threshold is 75% (separate pool) | attendance_engine | missing | Yes | — | NMC GMER 2019 §9.3 |
| ATT-NMC-013 | AETCOM attendance tracked separately from theory and practical | attendance_engine | missing | Yes | — | — |
| ATT-NMC-014 | Foundation Course attendance tracked separately | attendance_engine | missing | Yes | — | — |
| ATT-NMC-015 | Multi-phase subject (Community Medicine) aggregates attendance across phases | attendance_engine | missing | Yes | — | — |
| ATT-NMC-016 | Principal can grant attendance exemption with audit-logged reason | attendance_engine | missing | Yes | — | — |
| ATT-NMC-017 | Exemption is audit-logged with reason, approver, and timestamp | attendance_engine | missing | Yes | — | — |
| ATT-NMC-018 | Attendance denominator counts ONLY conducted sessions, NEVER planned | attendance_engine | missing | Yes | — | — |
| ATT-NMC-019 | Cancelled session does not count toward attendance denominator | attendance_engine | missing | Yes | — | — |
| ATT-NMC-020 | Late arrival (configurable threshold) counts as half-attendance if configured | attendance_engine | missing | Yes | — | — |
| ATT-001 | Mark attendance via manual roll call | attendance_engine | missing | Yes | — | — |
| ATT-002 | Mark attendance via QR code scan | attendance_engine | missing | Yes | — | — |
| ATT-003 | Mark attendance via RFID | attendance_engine | missing | No | Phase 2.5 | RFID hardware integration — no physical device available for testing |
| ATT-004 | Mark attendance via face recognition | attendance_engine | missing | No | Phase 3 | ML model required; not scoped for Phase 2 |
| ATT-005 | Mark attendance via GPS (with geofence validation) | attendance_engine | missing | No | Phase 2.5 | Mobile app geofence — requires mobile client |
| ATT-006 | Mark attendance via biometric | attendance_engine | missing | No | Phase 3 | Biometric hardware — not scoped for Phase 2 |
| ATT-007 | Attendance status: present, absent, late, excused, medical, official_duty | attendance_engine | missing | Yes | — | — |
| ATT-008 | Attendance percentage calculated correctly | attendance_engine | missing | Yes | — | — |
| ATT-009 | At-risk student list correctly identifies students below threshold | attendance_engine | missing | Yes | — | — |
| ATT-010 | Attendance trajectory prediction works (improving/declining/stable) | attendance_engine | missing | Yes | — | — |
| ATT-E001 | Two faculty mark same student differently for same event — last write wins by timestamp | attendance_engine | missing | Yes | — | — |
| ATT-E002 | Offline attendance with timestamp 2 hours after session end — flagged for faculty review, not auto-rejected | attendance_engine | missing | No | Phase 2.5 | Offline mobile sync feature deferred (ADR-028) |
| ATT-E003 | Duplicate attendance entry (same student, same event) is rejected | attendance_engine | missing | Yes | — | — |
| ATT-E004 | Attendance marked for cancelled event — flagged for admin review | attendance_engine | missing | Yes | — | — |
| ATT-E005 | Bulk attendance change (>20 students marked absent at once) triggers confirmation | attendance_engine | missing | Yes | — | — |
| ATT-E006 | Attendance correction window: faculty can correct within 24h, after that needs HOD approval | attendance_engine | missing | Yes | — | — |
| ATT-E007 | Student with disability accommodation: uses adjusted threshold per Dean approval | attendance_engine | missing | Yes | — | — |
| ATT-E008 | Emergency override (pandemic): temporary threshold reduction applies | attendance_engine | missing | Yes | — | — |
| ATT-E009 | Integration session attendance category inherits primary subject's category | attendance_engine | missing | Yes | — | — |
| ATT-E010 | Lateral entry student: prior phase attendance not included in current pct calculation | attendance_engine | missing | Yes | — | — |
| ATT-E011 | Detained student: attendance resets for repeated phase, prior phase retained as history | attendance_engine | missing | Yes | — | — |
| ATT-E012 | Section change mid-year: attendance from both sections aggregated | attendance_engine | missing | Yes | — | — |
| ATT-E013 | Multiple faculty per event: any faculty in faculty_ids can mark attendance | attendance_engine | missing | Yes | — | — |
| ATT-E014 | Faculty resignation: future sessions reassigned, past sessions retain original faculty_id | attendance_engine | missing | Yes | — | — |
| ATT-E015 | Phase transition: provisional status until prior exam results published | attendance_engine | missing | Yes | — | — |
| ATT-E016 | Concurrent attendance writes from two devices: unique constraint prevents duplicates | attendance_engine | missing | Yes | — | — |
| ATT-E017 | QR code reused: server rejects scans outside time window | attendance_engine | missing | No | Phase 2.5 | QR mobile client validation — requires mobile app |
| ATT-E018 | QR code HMAC tampering: server rejects invalid signatures | attendance_engine | missing | No | Phase 2.5 | HMAC validation implemented server-side; mobile client deferred |
| ATT-E019 | GPS attendance outside geofence: marked but flagged for review | attendance_engine | missing | No | Phase 2.5 | GPS geofence requires mobile client |
| ATT-E020 | Same student scans QR from two different devices: second scan rejected | attendance_engine | missing | No | Phase 2.5 | Requires mobile client QR scanning |
| ATT-SYNC-001 | Offline attendance entry persists in SQLite | attendance_engine | missing | No | Phase 2.5 | Offline mobile sync deferred (ADR-028) |
| ATT-SYNC-002 | Sync on connectivity restoration syncs oldest first | attendance_engine | missing | No | Phase 2.5 | Offline mobile sync deferred (ADR-028) |
| ATT-SYNC-003 | Per-entry transactional sync (interruption doesn't lose later entries) | attendance_engine | missing | No | Phase 2.5 | Offline mobile sync deferred (ADR-028) |
| ATT-SYNC-004 | Failed sync entry retried 3x with exponential backoff | attendance_engine | missing | No | Phase 2.5 | Offline mobile sync deferred (ADR-028) |
| ATT-SYNC-005 | Sync conflict (same student, same event, different status): later timestamp wins | attendance_engine | missing | No | Phase 2.5 | Offline mobile sync deferred (ADR-028) |
| ATT-SYNC-006 | Sync report visible to user (X synced, Y pending, Z failed) | attendance_engine | missing | No | Phase 2.5 | Offline mobile sync deferred (ADR-028) |
| ATT-SYNC-007 | Power outage during sync: resumes from last unacknowledged record | attendance_engine | missing | No | Phase 2.5 | Offline mobile sync deferred (ADR-028) |

### EXAMINATION MANAGEMENT (A-13)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| EXM-NMC-001 | Hall ticket eligibility requires theory ≥75% AND practical ≥80% for ALL subjects | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-002 | Hall ticket eligibility requires logbook submitted AND assessed | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-003 | Hall ticket eligibility requires minimum IA tests completed per subject | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-004 | Hall ticket eligibility requires AETCOM IA completed per phase | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-005 | Hall ticket eligibility requires certifiable competencies signed off | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-006 | Hall ticket eligibility requires fee clearance | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-007 | Logbook contributes up to 20% of IA marks | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-008 | OSPE used for pre-clinical and para-clinical subjects | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-009 | OSCE used for clinical subjects | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-010 | End-of-posting clinical assessment mandatory after every posting | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-011 | NExT eligibility additionally requires elective Block 1 and Block 2 logbooks | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-012 | DOPS assessment type supported for clinical postings | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-013 | mini-CEX assessment type supported for clinical postings | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-NMC-014 | AETCOM IA has both written and OSCE/viva components | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-001 | Create exam schedule | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-002 | Generate hall tickets for eligible students | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-003 | Hall ticket NOT generated for ineligible student | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-004 | Principal exemption flow: ineligible student gets hall ticket with audit log | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-005 | Mark entry by faculty, moderation by HOD | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-006 | Result publication with student notification | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-007 | Supplementary exam eligibility correctly determined | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-008 | OSPE station-level marks correctly aggregated | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-009 | OSCE station-level marks correctly aggregated | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-010 | Grace marks policy correctly applied | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-E001 | Student with partial pass (theory pass, practical fail): can sit supplementary practical only | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-E002 | Supplementary exam doesn't re-check current attendance (uses original attempt's) | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-E003 | Hall ticket race condition: distributed lock prevents duplicate generation | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-E004 | NExT eligibility recalculated after attendance correction | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-E005 | Exam invalidated due to malpractice: results marked invalidated, re-exam linked | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-E006 | Different assessment types use different scoring scales (integer, decimal, qualitative) | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-E007 | DOPS uses integer rating 1-9, OSCE uses half-points, theory uses integers 0-100 | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |
| EXM-E008 | Eligibility batch generation: idempotent, repeated runs produce same result | examination_management | missing | No | Phase 3 | Examination module is Phase 3 scope |

### CALENDAR & PLANNING (Phase 1B — A-04, A-05, A-06, A-07)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| CAL-001 | Create schedule calendar events with validations (category, phase, type) | academic_calendar | missing | Yes | — | — |
| CAL-E001 | Rescheduling maintaining parent link | academic_calendar | missing | Yes | — | — |
| CAL-E002 | Cancellation recording reason and actor | academic_calendar | missing | Yes | — | — |
| CAL-E003 | Bulk generation idempotency | academic_calendar | missing | Yes | — | — |
| CAL-E004 | Holiday calendar conflict detection | academic_calendar | missing | Yes | — | — |
| CAL-E005 | Faculty leave conflict detection at scheduling time | academic_calendar | missing | Yes | — | — |
| CAL-E006 | Room/lab double-booking prevention | academic_calendar | missing | Yes | — | — |
| CAL-E007 | Phase transition boundary events validation | academic_calendar | missing | Yes | — | — |
| CAL-E008 | Integration sessions map secondary courses via event_courses join table | academic_calendar | missing | Yes | — | — |
| LPN-001 | Create lesson plan with curriculum scoping and composite FK | lesson_plans | missing | Yes | — | — |
| LPN-002 | Lesson plan version updates incrementing version and toggling current flag | lesson_plans | missing | Yes | — | — |
| LPN-003 | Submit lesson plan for approval initiating workflow instance and denormalizing status | lesson_plans | missing | Yes | — | — |
| LPN-E001 | Lesson plan revision retains conducted sessions reference to older version | lesson_plans | missing | Yes | — | — |
| LPN-E002 | Log conducted session against unapproved lesson plan yields compliance warning | lesson_plans | missing | Yes | — | — |
| SES-001 | Log conducted session with actual hours and multiple faculty join table | session_tracking | missing | Yes | — | — |
| SES-002 | Nullable lesson plan with session reason is accepted | session_tracking | missing | Yes | — | — |
| SES-003 | Syllabus coverage calculation for competencies, hours, and topics | session_tracking | missing | Yes | — | — |
| FC-NMC-001 | Foundation Course scheduled as 1-month block at Phase I start | foundation_course_aetcom | missing | Yes | — | — |
| ECE-NMC-001 | ECE event type allowed only in Phase I | foundation_course_aetcom | missing | Yes | — | — |
| ECE-NMC-002 | Clinical postings event type NOT allowed in Phase I | foundation_course_aetcom | missing | Yes | — | — |
| AET-NMC-001 | AETCOM session event type supported | foundation_course_aetcom | missing | Yes | — | — |
| AET-NMC-005 | AETCOM completion required per phase before progression | foundation_course_aetcom | missing | Yes | — | — |

### DIGITAL LOGBOOK (A-10)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| LOG-NMC-001 | Logbook covers ALL subjects of current phase (not just clinical) | digital_logbook | missing | Yes | — | — |
| LOG-NMC-002 | Logbook covers Foundation Course section | digital_logbook | missing | Yes | — | — |
| LOG-NMC-003 | Logbook covers AETCOM sections per phase | digital_logbook | missing | Yes | — | — |
| LOG-NMC-004 | Logbook covers ECE sections (Phase I) | digital_logbook | missing | Yes | — | — |
| LOG-NMC-005 | Logbook covers Elective Block 1 and Block 2 (Phase III Part I) | digital_logbook | missing | Yes | — | — |
| LOG-NMC-006 | Logbook entry contains competency_code, level (K/KH/SH/P), is_core | digital_logbook | missing | Yes | — | — |
| LOG-NMC-007 | Faculty sign-off required (faculty_initials, faculty_date) | digital_logbook | missing | Yes | — | — |
| LOG-NMC-008 | Student sign-off required (student_initials) | digital_logbook | missing | Yes | — | — |
| LOG-NMC-009 | Attempt type tracked: F (first), R (repeat), Re (remedial) | digital_logbook | missing | Yes | — | — |
| LOG-NMC-010 | Rating tracked: B (below), M (meets), E (exceeds) OR numerical | digital_logbook | missing | Yes | — | — |
| LOG-NMC-011 | Faculty decision tracked: C (complete), R (repeat), Re (remedial) | digital_logbook | missing | Yes | — | — |
| LOG-NMC-012 | Logbook submission is prerequisite for summative exam | digital_logbook | missing | Yes | — | — |
| LOG-NMC-013 | Logbook assessment contributes up to 20% of IA marks | digital_logbook | missing | Yes | — | — |
| LOG-NMC-014 | Logbook IA contribution is zero if logbook incomplete | digital_logbook | missing | Yes | — | — |
| LOG-E001 | Backdated entry within 7 days: accepted without flag | digital_logbook | missing | Yes | — | — |
| LOG-E002 | Backdated entry 8-30 days: accepted but flagged for faculty review | digital_logbook | missing | Yes | — | — |
| LOG-E003 | Backdated entry >30 days: requires HOD approval | digital_logbook | missing | Yes | — | — |
| LOG-E004 | Future-dated entry rejected | digital_logbook | missing | Yes | — | — |
| LOG-E005 | Field-level offline merge: student fields and faculty fields merged separately | digital_logbook | missing | No | Phase 2.5 | Offline mobile logbook sync deferred (ADR-028) |
| LOG-E006 | Faculty resignation: pending sign-offs delegated to HOD | digital_logbook | missing | Yes | — | — |
| LOG-E007 | Large backlog sync (100+ entries from rural posting): per-entry transactional | digital_logbook | missing | No | Phase 2.5 | Offline mobile sync deferred (ADR-028) |
| LOG-E008 | Detained student: prior attempt logbook retained as read-only history | digital_logbook | missing | Yes | — | — |

### LEAVE MANAGEMENT (A-12)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| LEV-001 | Submit leave request of type (medical, academic, casual, other) | leave_management | missing | Yes | — | — |
| LEV-002 | Approved leave request triggers leave_service.on_approval() hook | leave_management | missing | Yes | — | — |
| LEV-003 | Approved leave materializes attendance rows with status medical/excused | leave_management | missing | Yes | — | — |
| LEV-004 | Leave approval workflow integration via workflow_instance_id | leave_management | missing | Yes | — | — |
| LEV-E001 | Leave request spanning existing conducted sessions raises validation check | leave_management | missing | Yes | — | — |

### ELECTIVES (A-08)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| EL-NMC-001 | Electives configured as 2-month block after Phase III Part I exam | electives (F-00 section) | missing | Yes | — | — |
| EL-NMC-004 | Elective allocation workflow respects capacity limits with row-level lock | electives (F-00 section) | missing | Yes | — | — |
| EL-NMC-006 | Elective 75% attendance threshold enforced | electives (F-00 section) | missing | Yes | — | — |
| EL-NMC-007 | Elective logbook entries unified with main logbook entries table | electives (F-00 section) | missing | Yes | — | — |
| EL-NMC-008 | Elective allocation uniqueness UNIQUE (student_id, block) is enforced | electives (F-00 section) | missing | Yes | — | — |
| ELEC-001 | Create elective: valid payload inserts row, returns ElectiveResponse | electives | passing | Yes | — | Implemented Session 9 |
| ELEC-002 | Submit student preferences: full-block replace, ranks 1-5, idempotent on re-submit | electives | passing | Yes | — | Implemented Session 9 |
| ELEC-003 | FCFS allocation: 10 students, 3 electives cap=4, expected allocation matches ADR-034 worked example | electives | missing | Yes | — | Integration test stub pending |
| ELEC-004 | Ranked allocation: 10 students, 3 electives cap=4, rank-pass result matches ADR-034 worked example | electives | missing | Yes | — | Integration test stub pending |
| ELEC-005 | Reallocation additive mode: only unallocated students assigned, existing allocations untouched | electives | missing | Yes | — | Integration test stub pending |
| ELEC-006 | Reallocation full mode: all existing allocations cleared, fresh allocation run | electives | missing | Yes | — | Integration test stub pending |
| ELEC-007 | Allocation run produces elective_allocation_runs audit row with correct totals | electives | missing | Yes | — | Integration test stub pending |
| ELEC-008 | Concurrent allocation triggers don't double-allocate: row-level FOR UPDATE serialises runs | electives | missing | No | Phase 2.5 | Concurrent load testing requires infrastructure setup (ADR-034) |
| ELEC-009 | Dry-run allocation: computes result, writes no rows, returns same counts as live | electives | missing | Yes | — | Integration test stub pending |
| ELEC-NMC-001 | Elective duration enforced: two blocks of 2 weeks each within Phase III Part I (NMC CBME 2019 Reg 7) | electives | missing | Yes | — | — |
| ELEC-NMC-002 | Student must be allocated at least one clinical-category elective across both blocks | electives | missing | Yes | — | — |
| ELEC-NMC-003 | Reflection logbook entry required per elective block before NExT eligibility | electives | missing | Yes | — | — |
| ELEC-NMC-004 | Faculty supervisor must be assigned per elective per student | electives | missing | Yes | — | — |
| ELEC-E001 | Student submits preferences twice: second submission replaces first (soft-delete + re-insert) | electives | passing | Yes | — | Implemented Session 9 |
| ELEC-E002 | Tie-breaking: two preferences share same submitted_at; deterministic hash of student_id breaks tie | electives | passing | Yes | — | Implemented Session 9 |
| ELEC-E003 | Student withdraws after allocation: capacity_remaining incremented, slot freed | electives | missing | Yes | — | — |
| ELEC-E004 | Capacity changes between dry-run and live run: live run uses locked capacity, not dry-run snapshot | electives | missing | Yes | — | — |
| ELEC-E005 | Student tries to submit preference for Block 1 after Block 1 allocation exists: SNX-ELEC-002 raised | electives | missing | Yes | — | — |
| ELEC-E006 | Preferences submitted with duplicate rank position in same block: validation error raised | electives | missing | Yes | — | — |
| ELEC-E007 | Preferences submitted with elective_id belonging to wrong block: validation error raised | electives | passing | Yes | — | Implemented Session 9 |

### DOAP SKILLS (A-09)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| DOAP-NMC-001 | DOAP session record contains stage (D/O/A/P) and rating (B/M/E) | doap_skills (F-00) | passing | Yes | — | Implemented Session 10 |
| DOAP-NMC-006 | DOAP session record contains nmc_level (K/KH/SH/P) and is_core | doap_skills (F-00) | passing | Yes | — | Implemented Session 10 |
| DOAP-E001 | DOAP sign-off is allowed post-session date | doap_skills (F-00) | passing | Yes | — | Implemented Session 10 |
| DOAP-001 | Record D stage with C decision creates record and logbook entry | doap_skills | passing | Yes | — | Implemented Session 10 |
| DOAP-002 | Record O stage requires preceding D certified (rejection if not) | doap_skills | passing | Yes | — | Implemented Session 10 |
| DOAP-003 | Record A stage requires preceding O certified | doap_skills | passing | Yes | — | Implemented Session 10 |
| DOAP-004 | Record P stage requires preceding A certified | doap_skills | passing | Yes | — | Implemented Session 10 |
| DOAP-005 | Re-attempt after R decision (attempt_type=R, same stage) | doap_skills | passing | Yes | — | Implemented Session 10 |
| DOAP-006 | Remediation workflow auto-created on Re decision | doap_skills | missing | Yes | — | Integration test stub pending |
| DOAP-007 | Evidence asset IDs linked correctly | doap_skills | missing | Yes | — | Integration test stub pending |
| DOAP-008 | Auto-creation of logbook_entries on every DOAP record | doap_skills | missing | Yes | — | Integration test stub pending |
| DOAP-NMC-001 | Stage progression D→O→A→P enforced (no skipping) | doap_skills | passing | Yes | — | Implemented Session 10 |
| DOAP-NMC-002 | Faculty decision required for every record (cannot be null) | doap_skills | passing | Yes | — | Implemented Session 10 |
| DOAP-NMC-003 | Rating B implies decision R or Re (cannot be C) | doap_skills | passing | Yes | — | Implemented Session 10 |
| DOAP-E001 | Backward stage record (refresher D after reaching O) - allowed | doap_skills | passing | Yes | — | Implemented Session 10 |
| DOAP-E002 | Faculty decision Re with no active remediation programme - handle gracefully | doap_skills | missing | Yes | — | — |
| DOAP-E003 | Stage skip attempt (P without prior A) - must reject with specific error | doap_skills | passing | Yes | — | Implemented Session 10 |

### FOUNDATION COURSE SYNC / AETCOM SYNC (A-07)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| FCS-001 | Foundation Course records completed hours recomputed automatically from attendance | foundation_course_sync | missing | Yes | — | — |
| FCS-002 | Trigger blocks completed hours reduction if signoff received | foundation_course_sync | missing | Yes | — | — |
| AES-001 | AETCOM records status recomputed automatically from attendance | aetcom_sync | missing | Yes | — | — |

### ACCOMMODATIONS (A-11)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| ACC-001 | Attendance accommodation supports blanket and per-category threshold overrides | accommodations | missing | Yes | — | — |
| ACC-002 | Attendance percentage calculated against override thresholds in reports | accommodations | missing | Yes | — | — |

### CRMI / INTERNSHIP (M-03 — Phase 4)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| CRMI-NMC-001 | All 7 mandatory rotations enforced | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-002 | General Medicine rotation: 2 months (with 15 days Psychiatry OR TB&Resp) | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-003 | General Surgery rotation: 2 months (with 15 days Orthopaedics) | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-004 | OBG rotation: 2 months | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-005 | Paediatrics rotation: 1 month | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-006 | Community Medicine rotation: 2 months (including rural) | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-007 | Emergency/Casualty rotation: 1 month | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-008 | Elective rotation: 15 days from approved list | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-009 | 75% attendance enforced PER ROTATION (not aggregate) | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-010 | Maximum 15 days leave across ENTIRE CRMI period | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-011 | Intern at 15 days leave cannot apply for further leave | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-012 | Intern at 12 days leave receives early warning | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-013 | Rotation extension for attendance shortfall: extends to reach 75% | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-014 | Subsequent rotations shift after extension | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-015 | Leave cap does NOT reset after extension | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-016 | CRMI Completion Certificate requires ALL rotations satisfactorily complete | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-017 | End-of-rotation assessment mandatory per rotation | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-018 | Intern logbook separate from MBBS student logbook | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-019 | Only ONE active CRMI enrollment per student | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |
| CRMI-NMC-020 | Transfer-in CRMI requires NOC from previous hospital | internship_crmi | missing | No | Phase 4 | Full CRMI module is Phase 4 scope |

### CURRICULUM VERSIONING (A-02)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| CUR-001 | JMN 2023 admission batch uses NMC CBME 2019 | curriculum_versioning | missing | Yes | — | — |
| CUR-002 | JMN 2024 admission batch uses NMC CBME 2023 | curriculum_versioning | missing | Yes | — | — |
| CUR-003 | Both curricula coexist; no conflict in competency codes | curriculum_versioning | missing | Yes | — | — |
| CUR-004 | Competency code uniqueness is scoped per curriculum, not global | curriculum_versioning | missing | Yes | — | — |
| CUR-005 | Curriculum migration: bridge courses correctly applied | curriculum_versioning | missing | No | Phase 3 | Full curriculum migration engine is Phase 3 scope (ADR-019) |
| CUR-006 | Credit map preserves equivalence between curricula | curriculum_versioning | missing | No | Phase 3 | Full curriculum migration engine is Phase 3 scope (ADR-019) |
| CUR-007 | Migration impact analysis shows affected students/courses | curriculum_versioning | missing | No | Phase 3 | Full curriculum migration engine is Phase 3 scope (ADR-019) |

### MULTI-TENANCY & SECURITY (F-00)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| TNT-001 | API request with no tenant context is rejected | multi_tenancy | missing | Yes | — | — |
| TNT-002 | User from tenant A cannot read tenant B data | multi_tenancy | missing | Yes | — | — |
| TNT-003 | User from tenant A cannot write to tenant B | multi_tenancy | missing | Yes | — | — |
| TNT-004 | RLS policy enforces isolation at DB level even if middleware fails | multi_tenancy | missing | Yes | — | — |
| TNT-005 | JWT with tampered tenant_id is rejected | multi_tenancy | missing | Yes | — | — |
| TNT-006 | Aggregate analytics at super-admin level can see across tenants | multi_tenancy | missing | Yes | — | — |
| TNT-007 | Cross-tenant faculty (same person in two tenants): separate sessions | multi_tenancy | missing | Yes | — | — |

### AUDIT LOG (F-00)

| Test ID | Description (from COVERAGE_MANIFEST) | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------------------------------------|--------|----------------|---------------------|-----------------|---------------------|
| AUD-001 | Every data modification creates an audit_log entry | audit_log | missing | Yes | — | — |
| AUD-002 | audit_log table cannot be UPDATEd (trigger blocks) | audit_log | missing | Yes | — | — |
| AUD-003 | audit_log table cannot be DELETEd (trigger blocks) | audit_log | missing | Yes | — | — |
| AUD-004 | Audit entry contains: who, what, when, IP, device | audit_log | missing | Yes | — | — |
| AUD-005 | Old and new values stored as JSONB | audit_log | missing | Yes | — | — |
| AUD-006 | Sensitive fields (passwords, OTPs) NOT logged | audit_log | missing | Yes | — | — |
| AUD-007 | Exemption grants logged with reason and approver | audit_log | missing | Yes | — | — |

---

## Deferral Impact Analysis

| Metric | Count |
|--------|-------|
| Baseline total tests in manifest | 239 |
| Baseline "missing" (not in codebase at all) | ~219 |
| Tests already passing | 20 |
| After deferral acknowledgement — deferred to Phase 2.5 | 21 |
| After deferral acknowledgement — deferred to Phase 3/4 | 100 |
| **Remaining "must implement" for Phase 2 completion** | **98** |

**Phase 2 completion target: 98 tests must pass (20 already passing, 78 remaining to implement)**

---

## Notes on Categorisation Decisions

1. **ATT-003 is QR-based marking** (description: "Mark attendance via QR code scan") — NOT RFID. The Phase 2 Complete Plan had it correctly at line 997. My earlier plan summary erroneously labelled it RFID. It is categorised as **Must pass Phase 2** (no hardware dependency for server-side QR validation).

2. **ATT-003 (RFID) from original manifest** — The original manifest section has ATT-003 as "Mark attendance via RFID". This is a DIFFERENT numbering than R2.1's proposed additions. The original section is what exists in the manifest. ATT-003 = RFID in the EXISTING manifest → deferred Phase 2.5.

3. **EXM-NMC-011** already in NMC_COMPLIANCE_TESTS.md (present) — not in missing-from-doc list. Examination module entirely deferred to Phase 3.

4. **ELEC-008** already has `deferred_to: "Phase 2.5"` in manifest — consistent with this categorisation.

5. **DOAP tests from F-00 section** (DOAP-NMC-001, DOAP-NMC-006, DOAP-E001) are a separate, earlier entry in the manifest from the more detailed `doap_skills` section added in Session 10. Both must be satisfied.
