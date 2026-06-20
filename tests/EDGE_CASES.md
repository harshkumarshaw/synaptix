# Synaptix Edge Cases — Comprehensive Catalogue

> **Every edge case here MUST have a corresponding test.** The Testing Agent reads this file and implements every case.
>
> Last updated: 2026-06-18
> Total cases: 100+ (will grow as discovered)

## How to Use This Document

Each edge case has:
- **ID** — stable identifier used in tests and code references
- **Category** — type of edge case
- **Severity** — Critical / High / Medium / Low
- **Audit Reference** — where this came from
- **Description** — what scenario this covers
- **Expected Behaviour** — what the system must do
- **Test Reference** — link to test file

---

## Category 1: Student Lifecycle Edge Cases

### EC-001: Lateral Entry / Transfer-In Student [CRITICAL]
**Audit Ref:** v4-AUDIT-E1
**Scenario:** A student transfers from another medical college into Phase II at JMN. They have completed Phase I elsewhere with attendance records, logbook, and competency completions.
**Expected:**
- Admin uploads transfer documents (attendance cert, logbook completion cert, competency record)
- Student record created starting from Phase II
- Phase I records marked "transferred — verified by Principal"
- Phase I logbook shows "Completed at [source institution]" — read-only
- Phase I attendance NOT included in current percentage calculations
- Only Phase II+ attendance counted in AOIP
**Test:** `tests/integration/lifecycle/test_lateral_entry.py`

### EC-002: Detention / Year-Back Student [CRITICAL]
**Audit Ref:** v4-AUDIT-E2
**Scenario:** Student fails Phase II exam, must repeat Phase II with the next batch.
**Expected:**
- New batch assignment for the repeated phase
- `original_batch_id` retained
- Attendance resets for the repeated phase
- Logbook entries from failed attempt retained as "Prior Attempt" (read-only)
- Competencies achieved persist (faculty can re-verify or accept)
- IA marks from failed attempt archived
- Student is in Phase II of new batch, NOT Phase III of original batch
**Test:** `tests/integration/lifecycle/test_detention.py`

### EC-003: Student Dies or Medical Emergency [MEDIUM]
**Audit Ref:** v5-NEW
**Scenario:** Active student dies or enters long-term coma.
**Expected:**
- Lifecycle state: `active` → `deceased` or `medically_withdrawn`
- All automated notifications cease immediately
- Records preserved permanently (exempted from normal retention)
- Parent portal access maintained indefinitely
- Workflow requires Principal + Dean approval
**Test:** `tests/integration/lifecycle/test_critical_emergency.py`

### EC-004: Student Name Change [LOW]
**Audit Ref:** v5-NEW
**Scenario:** Student changes legal name (marriage, court order, gender transition).
**Expected:**
- `current_name` updated
- `name_history[JSONB]` retained
- Future documents use new name
- Historical documents unchanged (snapshot in time)
**Test:** `tests/unit/student/test_name_change.py`

### EC-005: Duplicate Enrollment Detection [HIGH]
**Audit Ref:** v5-NEW
**Scenario:** Same person tries to enroll twice (different roll numbers, same Aadhaar/phone).
**Expected:**
- Unique constraint on `(tenant_id, aadhaar_hash)` prevents duplicate
- Unique constraint on `(phone_number, program_id)` prevents same phone in two programs
- Admission validates no active enrollment in any NMC-regulated program before MBBS admission
**Test:** `tests/security/lifecycle/test_duplicate_enrollment.py`

---

## Category 2: Attendance Edge Cases

### EC-010: Two Faculty Mark Same Student Differently [HIGH]
**Audit Ref:** v4-AUDIT-E8
**Scenario:** Faculty A marks Student X "present" on web, Faculty B marks "absent" on mobile, same event.
**Expected:**
- Unique constraint on `(event_id, student_id)` prevents two records
- First write succeeds, second is UPDATE
- Last write wins by timestamp
- Audit log captures both writes
**Test:** `tests/integration/attendance/test_concurrent_marking.py`

### EC-011: Offline Attendance with Late Timestamp [MEDIUM]
**Audit Ref:** v4-AUDIT-F1
**Scenario:** Faculty marks attendance offline at 11:00 PM for a session that ended at 11:00 AM same day.
**Expected:**
- Record accepted
- Flagged for faculty review (`needs_review = true`)
- NOT auto-rejected
- Original timestamp preserved
**Test:** `tests/integration/attendance/test_late_offline_sync.py`

### EC-012: Bulk Attendance Error [HIGH]
**Audit Ref:** v4-AUDIT-3.10
**Scenario:** Faculty accidentally marks all 150 students absent (one-click error).
**Expected:**
- Bulk change >20 students triggers confirmation prompt
- "You are marking 150 students as ABSENT. Continue?"
- Within 24h: faculty can correct
- After 24h: HOD approval required
- All corrections logged
**Test:** `tests/integration/attendance/test_bulk_error.py`

### EC-013: Attendance Denominator [CRITICAL]
**Audit Ref:** v4-AUDIT-D3
**Scenario:** Timetable modified mid-phase; new sessions added retroactively.
**Expected:**
- Attendance percentage calculated against **conducted sessions only**, never planned
- Cancelled sessions excluded from denominator
- Future sessions excluded from denominator
**Test:** `tests/unit/attendance/test_denominator.py`

### EC-014: Integration Session Category [MEDIUM]
**Audit Ref:** v4-AUDIT-C4
**Scenario:** Horizontal integration session combining Anatomy (theory) and Medicine (clinical).
**Expected:**
- Event creator specifies primary `attendance_category`
- Theory-based integration: counts toward 75% theory pool
- Clinical-based integration: counts toward 80% practical pool
**Test:** `tests/integration/attendance/test_integration_category.py`

### EC-015: Student with Disability Accommodation [MEDIUM]
**Audit Ref:** v4-AUDIT-E6
**Scenario:** Student with documented disability has Dean-approved reduced threshold (e.g., 65% theory).
**Expected:**
- Per-student threshold override
- Medical documentation required
- Approval workflow: student → disability cell → Dean
- Audit trail
- Reports show actual % AND adjusted threshold
**Test:** `tests/integration/attendance/test_accommodation.py`

### EC-016: Pandemic / Emergency Override [MEDIUM]
**Audit Ref:** v4-AUDIT-E7
**Scenario:** NMC issues circular reducing attendance during pandemic.
**Expected:**
- Super Admin / Principal declares emergency period
- Thresholds temporarily reduced
- Online sessions count toward attendance (configurable)
- Phase duration extensions allowed
- All overrides linked to NMC circular reference
**Test:** `tests/integration/attendance/test_emergency_override.py`

### EC-017: QR Code Replay Attack [HIGH SECURITY]
**Audit Ref:** v5-NEW
**Scenario:** Student tries to scan QR code generated for an earlier session.
**Expected:**
- QR contains session_id, valid_from, valid_until, HMAC
- Server validates time window
- Scans outside window rejected with `SNX-ATT-401`
**Test:** `tests/security/attendance/test_qr_replay.py`

### EC-018: QR Code HMAC Tampering [HIGH SECURITY]
**Audit Ref:** v5-NEW
**Scenario:** Student tampers with QR payload to extend time window.
**Expected:**
- HMAC signature validated server-side
- Invalid signature → 401 rejection
- Tampering attempt logged in security audit
**Test:** `tests/security/attendance/test_qr_tampering.py`

### EC-019: Same Student, Two Devices [MEDIUM]
**Audit Ref:** v4-AUDIT-6.2
**Scenario:** Student scans QR on phone, then on borrowed tablet, same event.
**Expected:**
- Unique constraint on `(event_id, student_id)` prevents duplicate
- Second scan returns "Already marked at <time>"
- Device fingerprint logged for audit
**Test:** `tests/integration/attendance/test_multi_device.py`

### EC-020: Multi-Phase Subject Aggregation [MEDIUM]
**Audit Ref:** v4-AUDIT-C5
**Scenario:** Community Medicine taught across Phase I, II, III Part I, III Part II.
**Expected:**
- Attendance tracked per phase
- Exam eligibility aggregates across phases, weighted by contact hours
- Phase-specific reports available
**Test:** `tests/integration/attendance/test_multi_phase_subject.py`

---

## Category 3: Logbook Edge Cases

### EC-030: Backdated Entry [HIGH]
**Audit Ref:** v4-AUDIT-D2
**Scenario:** Student adds entry on June 15 for activity claimed on June 1.
**Expected:**
- Gap ≤7 days: accepted without flag
- Gap 8-30 days: accepted, flagged for faculty review, auto-notification to faculty
- Gap >30 days: requires HOD approval
- All backdated entries: `backdated=true`, audit trail with both dates
**Test:** `tests/integration/logbook/test_backdating.py`

### EC-031: Future-Dated Entry [LOW]
**Audit Ref:** v5-NEW
**Scenario:** Student creates entry with `date_completed` in the future.
**Expected:**
- Rejected at validation layer (Pydantic)
- Error: "date_completed cannot be in the future"
**Test:** `tests/unit/logbook/test_future_date.py`

### EC-032: Field-Level Offline Merge [HIGH]
**Audit Ref:** v4-AUDIT-D4
**Scenario:** Student edits `activity_description` on phone. Faculty edits `feedback_notes` on tablet. Both sync later.
**Expected:**
- Field-level merge, not record-level
- Student fields (activity_description, student_initials, student_reflection) from student device
- Faculty fields (feedback_notes, rating, faculty_decision, attempt_type) from faculty device
- If same field edited by both: flag for manual resolution
**Test:** `tests/integration/logbook/test_field_level_merge.py`

### EC-033: Faculty Resignation Pending Sign-Off [HIGH]
**Audit Ref:** v4-AUDIT-E5 + O1
**Scenario:** Faculty conducted DOAP session, resigns before signing off student logbooks.
**Expected:**
- Faculty unavailable >7 days: HOD can delegate sign-off
- Delegated sign-off records both `original_faculty_id` and `signing_faculty_id`
- Audit trail captures delegation reason
**Test:** `tests/integration/logbook/test_delegated_signoff.py`

### EC-034: Large Offline Sync Backlog [HIGH]
**Audit Ref:** v4-AUDIT-F1
**Scenario:** Student in 4-week rural posting returns with 100+ logbook entries to sync.
**Expected:**
- Per-entry transactional sync (not batch)
- Failed entries retried 3x with exponential backoff
- Failed entries do NOT block subsequent entries
- Sync report visible: X synced, Y pending, Z failed
**Test:** `tests/integration/logbook/test_large_sync.py`

### EC-035: Logbook IA Contribution Edge Cases [MEDIUM]
**Audit Ref:** v4-AUDIT-F5
**Scenario:** Various states of logbook completion affect IA.
**Expected:**
- Logbook complete: 20% of total IA marks (theory + practical combined)
- Logbook incomplete: 0% contribution
- Multiple assessments: latest score used
- Configurable per institution per subject (0-20% range)
**Test:** `tests/unit/logbook/test_ia_contribution.py`

---

## Category 4: Exam & Result Edge Cases

### EC-040: Partial Pass in Supplementary [HIGH]
**Audit Ref:** v4-AUDIT-E3
**Scenario:** Student passes theory but fails practical in original attempt.
**Expected:**
- `component_pass_status` per subject: theory_pass, practical_pass, clinical_pass independent
- Supplementary types: `Supplementary_Theory`, `Supplementary_Practical`, `Supplementary_Clinical`
- Supplementary doesn't re-check current attendance (uses original attempt's)
**Test:** `tests/integration/exam/test_partial_pass.py`

### EC-041: Hall Ticket Race Condition [MEDIUM]
**Audit Ref:** v4-AUDIT-F3
**Scenario:** Two admin staff trigger hall ticket generation for same batch concurrently.
**Expected:**
- Distributed lock (Redis or DB advisory lock) per batch
- Only one generation runs at a time
- Generated records timestamped and immutable
**Test:** `tests/integration/exam/test_hall_ticket_lock.py`

### EC-042: Exam Invalidation [MEDIUM]
**Audit Ref:** v4-AUDIT-O5
**Scenario:** Exam cancelled due to paper leak.
**Expected:**
- Status: `conducted` → `invalidated` (with reason and authority)
- All linked results: `is_invalidated = true`
- New exam linked as `reexam_of`
- Students not involved in malpractice can opt for original marks (institutional policy)
**Test:** `tests/integration/exam/test_invalidation.py`

### EC-043: Different Assessment Scoring Scales [MEDIUM]
**Audit Ref:** v4-AUDIT-3.6
**Scenario:** Different assessment types use different scales (integer, decimal, qualitative).
**Expected:**
- Theory written: integer 0-100
- OSCE station: decimal with half-points (e.g., 7.5)
- DOPS: integer rating 1-9
- Logbook assessment: decimal percentage 0-100
- AETCOM: qualitative (Satisfactory/Unsatisfactory) OR numeric
- Validation rules per assessment type enforced
**Test:** `tests/unit/exam/test_scoring_scales.py`

### EC-044: Back-to-Back Phase Transition [HIGH]
**Audit Ref:** v4-AUDIT-3.7
**Scenario:** Phase I ends in July, Phase II starts in August. Phase I results not yet published.
**Expected:**
- Provisional Phase II enrollment when new phase starts
- Attendance during provisional period flagged
- When Phase I results published:
  - Passed students: provisional → confirmed in Phase II
  - Failed students: detention workflow, moved back to Phase I
  - Provisional attendance reassigned retroactively
**Test:** `tests/integration/exam/test_phase_transition.py`

### EC-045: NExT Eligibility Recalculation [MEDIUM]
**Audit Ref:** v4-AUDIT-P2
**Scenario:** Attendance corrected after NExT eligibility check ran.
**Expected:**
- Eligibility is recalculated on next check
- Latest `next_eligibility` record is authoritative
- Older records archived but not deleted
**Test:** `tests/integration/exam/test_next_recalculation.py`

---

## Category 5: CRMI Edge Cases

### EC-050: CRMI Extension for Attendance Shortfall [HIGH]
**Audit Ref:** v4-AUDIT-E4
**Scenario:** Intern at 70% in General Medicine (below 75%).
**Expected:**
- Extension = days needed to reach 75% (assuming 100% attendance during extension)
- Subsequent rotations shift accordingly
- Leave cap (15 days) does NOT reset
- Total CRMI may exceed 12 months — actual duration recorded in completion cert
**Test:** `tests/integration/crmi/test_extension.py`

### EC-051: CRMI Leave Cap Enforcement [HIGH]
**Audit Ref:** v5-NEW
**Scenario:** Intern at 14 days leave applies for 2 more days.
**Expected:**
- At 12 days: early warning shown
- At 15 days: leave application blocked
- Attempt to exceed: rejected with `SNX-CRMI-LEAVE-001`
**Test:** `tests/integration/crmi/test_leave_cap.py`

### EC-052: Concurrent CRMI Registration [LOW]
**Audit Ref:** v4-AUDIT-O6
**Scenario:** Intern tries to register CRMI at two hospitals.
**Expected:**
- Unique constraint: one active CRMI per student
- Transfer-in requires NOC from previous hospital + Principal approval
**Test:** `tests/security/crmi/test_concurrent_registration.py`

---

## Category 6: Multi-Tenancy & Security Edge Cases

### EC-060: Cross-Tenant Token Tampering [CRITICAL SECURITY]
**Audit Ref:** v5-NEW
**Scenario:** Attacker modifies JWT `tenant_id` to access another tenant's data.
**Expected:**
- JWT signature validation catches tampering
- Tampered token rejected
- Even if signature bypass: RLS policy at DB level prevents query
- Security incident logged
**Test:** `tests/security/tenancy/test_jwt_tampering.py`

### EC-061: Faculty in Multiple Tenants [MEDIUM]
**Audit Ref:** v4-AUDIT-3.5
**Scenario:** Senior professor teaches at JMN AND IINR.
**Expected:**
- Separate faculty records per tenant
- `cross_tenant_faculty_link` table maps same person across tenants
- Super Admin can aggregate teaching load
- Faculty has separate login sessions per tenant
- `primary_tenant_id` for NMC reporting
**Test:** `tests/integration/tenancy/test_cross_tenant_faculty.py`

### EC-062: NMC Inspector Access [HIGH]
**Audit Ref:** v4-AUDIT-O2
**Scenario:** NMC inspector arrives for inspection, needs real-time access.
**Expected:**
- Principal creates time-limited inspector account (7 days)
- OTP authentication (no institutional credentials)
- Read-only scope: program being inspected
- All access logged in audit trail with `inspector` user type
- Auto-deactivation on expiry
**Test:** `tests/integration/security/test_inspector_access.py`

### EC-063: Right to Erasure vs Retention [HIGH]
**Audit Ref:** v4-AUDIT-S1
**Scenario:** Student requests data erasure (DPDP Act).
**Expected:**
- During retention period (7 years): soft delete, business data retained for accreditation
- After retention: personal identifiers anonymised (name, email, phone, Aadhaar hashed)
- Academic skeleton preserved (attendance %, marks, competencies — anonymised)
- Audit log subject to same anonymisation
**Test:** `tests/integration/dpdp/test_erasure.py`

### EC-064: WhatsApp Bot Impersonation [HIGH SECURITY]
**Audit Ref:** v4-AUDIT-F4
**Scenario:** Student's phone number reassigned to someone else.
**Expected:**
- WhatsApp bot requires periodic re-verification (every 30 days)
- Students can deactivate from web app
- Admin can revoke access
- Sensitive data (results, fees) requires in-session OTP
**Test:** `tests/integration/whatsapp/test_reverification.py`

### EC-065: Medical Leave Certificate Privacy [MEDIUM]
**Audit Ref:** v4-AUDIT-S2
**Scenario:** Medical certificate contains sensitive health info (pregnancy, mental health).
**Expected:**
- Certificate visible only to Dean/Principal and designated Medical Officer
- Faculty/HOD see only "Medical leave — verified by [Medical Officer]"
- DPDP Act compliance for sensitive personal data
**Test:** `tests/security/leave/test_medical_certificate_privacy.py`

---

## Category 7: Date / Time / Locale Edge Cases

### EC-070: Timezone Display Mismatch [MEDIUM]
**Audit Ref:** v5-NEW
**Scenario:** Faculty marks attendance at 8 AM IST. Database stores UTC (2:30 AM).
**Expected:**
- All timestamps stored UTC
- API responses include `timezone: "Asia/Kolkata"` in meta
- Frontend converts to IST for display
- `TIME` fields (session start/end) store IST directly
**Test:** `tests/unit/common/test_timezone.py`

### EC-071: Phone in Different Timezone [LOW]
**Audit Ref:** v5-NEW
**Scenario:** Student in border area has phone set to Bangladesh time (UTC+6).
**Expected:**
- Offline entry stores both local device time AND UTC
- Server uses UTC
- Device time for audit/dispute resolution
**Test:** `tests/integration/mobile/test_phone_timezone.py`

### EC-072: Academic Year Boundary [LOW]
**Audit Ref:** v5-NEW
**Scenario:** Intern's night duty starts June 30, 8 PM and ends July 1, 8 AM.
**Expected:**
- Attendance assigned to academic year of event's `date` (start date)
- Night duty starting June 30 → counts toward year ending June 30
**Test:** `tests/unit/attendance/test_year_boundary.py`

### EC-073: Daylight Saving Time [N/A]
**Note:** India does not observe DST. Tests skip DST scenarios.

---

## Category 8: Operational Edge Cases

### EC-080: Mid-Year Faculty Transfer [HIGH]
**Audit Ref:** v4-AUDIT-O1
**Scenario:** Faculty completes 60% of subject's sessions, resigns.
**Expected:**
- Future sessions reassigned to replacement
- Pending lesson plans reassigned
- Historical records retain original faculty_id
- Pending logbook sign-offs delegate to HOD
- Handover report generated
**Test:** `tests/integration/faculty/test_resignation.py`

### EC-081: NMC Inspection During Downtime [MEDIUM]
**Audit Ref:** v4-AUDIT-3.8
**Scenario:** System down during NMC inspection.
**Expected:**
- Nightly offline inspection pack PDF generated
- Stored on Principal's laptop
- Contains: attendance summaries, competency completion, faculty load, research output
- QR codes for live system access when connectivity returns
**Test:** Manual test, not automated. Documented in `docs/MANUAL_TESTS.md`.

### EC-082: Faculty Marks Wrong Batch [MEDIUM]
**Audit Ref:** v4-AUDIT-6.3
**Scenario:** Faculty selects MBBS 2024 instead of MBBS 2023, marks 150 students wrong batch.
**Expected:**
- Pre-populate batch from faculty's timetable
- If overridden: confirmation prompt
- Bulk reverse + remark with audit trail (admin action)
**Test:** `tests/integration/attendance/test_wrong_batch.py`

### EC-083: University Affiliation Change [LOW]
**Audit Ref:** v4-AUDIT-6.4
**Scenario:** JMN's affiliation changes from WBUHS to Nirmala Vishwa Vidyapeeth.
**Expected:**
- `program.affiliation` with effective dates
- Grading scheme versioned per affiliation period
- Transcripts show both affiliations for affected students
**Test:** `tests/integration/curriculum/test_affiliation_change.py`

### EC-084: Anti-Ragging Complaint [LOW]
**Audit Ref:** v4-AUDIT-6.6
**Scenario:** Student submits anonymous ragging complaint.
**Expected:**
- Complaint type: `ragging` in Student Success Centre
- Anonymous routing to Anti-Ragging Committee
- Committee sees content, not complainant identity
- UGC Anti-Ragging portal integration (Year 2)
**Test:** `tests/integration/student_success/test_ragging_complaint.py`

---

## Category 9: Data Integrity Edge Cases

### EC-090: Competency Code Collision Across Curricula [HIGH]
**Audit Ref:** v4-AUDIT-D1
**Scenario:** NMC CBME 2019 and 2023 both use code `AN-1.1` with different descriptions.
**Expected:**
- Uniqueness scoped to `(curriculum_id, subject_code, competency_code)`, NOT global
- All queries filter by `curriculum_id`
- Reports never conflate 2019 and 2023 competencies
**Test:** `tests/unit/competency/test_code_collision.py`

### EC-091: Migration Dependency Order [HIGH]
**Audit Ref:** v5-NEW
**Scenario:** Migration A creates `events` table. Migration B references `events`. Run B first.
**Expected:**
- Single linear migration chain (not per-service)
- `alembic upgrade head` in CI catches ordering issues
- Migration dependencies explicit in `depends_on`
**Test:** Migration smoke test in CI

### EC-092: Soft Delete + Unique Constraint [MEDIUM]
**Audit Ref:** v5-NEW
**Scenario:** User soft-deleted (deleted_at set). New user with same email tries to register.
**Expected:**
- Unique constraint: `UNIQUE (email) WHERE deleted_at IS NULL`
- Allows reuse of email after soft delete
- New user gets fresh ID, no record reuse
**Test:** `tests/unit/user/test_soft_delete_uniqueness.py`

---

## Category 10: Performance Edge Cases

### EC-100: Attendance Table at Scale [HIGH]
**Audit Ref:** v5-NEW (from feasibility)
**Scenario:** 100M+ rows in attendance table after 5 years.
**Expected:**
- Partitioning by `academic_year_id`
- Materialised view `attendance_summary` updated via trigger
- Dashboard reads from summary, never raw
- Archive partitions >3 years old to cold storage
**Test:** Load test in `tests/load/test_attendance_scale.py`

### EC-101: Exam Day Concurrent Eligibility Checks [MEDIUM]
**Audit Ref:** v5-NEW
**Scenario:** 150 students check NExT eligibility within 60 seconds on exam day.
**Expected:**
- Pre-generated nightly during exam season
- Live check only if cache >24h old
- Rate limit: 10 checks/min per batch
**Test:** Load test in `tests/load/test_eligibility_spike.py`

### EC-102: Slow Query Detection [LOW]
**Audit Ref:** v5-NEW
**Scenario:** Some queries take >2 seconds.
**Expected:**
- pg_stat_statements enabled
- Slow query log written to `docs/PERFORMANCE_LOG.md` weekly
- Performance Agent reviews and optimises
**Test:** Performance monitoring, not unit test

---

## Category 11: Workflow, MDM & Digital Asset Edge Cases

### EC-103: Definition Deactivated Mid-Workflow [HIGH]
**Audit Ref:** v5-NEW
**Scenario:** A workflow definition v1 is deactivated or a new version v2 is published while a v1 instance is in-flight.
**Expected:**
- In-flight instance continues using v1 definition reference until completion.
- New instances are created using v2 (since is_current = true on v2 and false on v1).
**Test:** `tests/unit/workflow/test_definition_versioning.py`

### EC-104: Concurrent Transition Submissions [HIGH]
**Audit Ref:** v5-NEW
**Scenario:** Two approvers submit transition approvals for the same workflow instance concurrently.
**Expected:**
- DB row lock prevents double-transition.
- One transition succeeds, the other fails with InvalidStateTransitionError.
**Test:** `tests/integration/workflow/test_full_lifecycle.py`

### EC-105: Soft-Deleted Current Assignee [HIGH]
**Audit Ref:** v5-NEW
**Scenario:** The user assigned to a pending workflow step is soft-deleted (resigned/transferred, audit ref AUDIT-O1).
**Expected:**
- Workflow service detects the assignee's soft-deleted status.
- Reassigns to HOD or triggers role-based open assignment.
**Test:** `tests/integration/workflow/test_full_lifecycle.py`

### EC-106: Cross-Tenant Definition/User Reference [CRITICAL SECURITY]
**Audit Ref:** v5-NEW
**Scenario:** Attacker attempts to create a workflow_instance in Tenant A referencing a workflow_definition or assignee in Tenant B.
**Expected:**
- Composite FK on (tenant_id, definition_id) or (tenant_id, current_assignee_id) rejects write at DB layer.
- Transaction is aborted with foreign key violation.
**Test:** `tests/security/workflow/test_tenant_isolation.py`

### EC-107: Duplicate Asset Upload [MEDIUM]
**Audit Ref:** v5-NEW
**Scenario:** A user uploads a file matching an existing file's SHA256 checksum in the tenant.
**Expected:**
- Creates a new digital_assets record but references existing path or creates new metadata node.
- Upload computes SHA256 for validation.
**Test:** `tests/unit/assets/test_asset_service.py`

---

## Category 12: Calendar & Planning Edge Cases

### EC-110: Rescheduled Event Parent Reference [MEDIUM]
**Scenario:** An event is rescheduled. A new event is created, and it must maintain a reference to the original event.
**Expected:**
- Original event status updated to 'rescheduled'.
- New event has `parent_event_id` pointing to the original event's ID.
**Test:** `tests/integration/test_calendar_engine.py`

### EC-111: Cancelled Event Audit Details [MEDIUM]
**Scenario:** An event is cancelled. It must record the reason and actor.
**Expected:**
- Status set to 'cancelled'.
- `cancellation_reason` and `cancelled_by` are recorded and non-null.
**Test:** `tests/integration/test_calendar_engine.py`

### EC-112: Bulk Schedule Generation Idempotency [HIGH]
**Scenario:** Admin triggers bulk schedule generation multiple times.
**Expected:**
- Idempotency keys or validation checks prevent duplicate calendar events from being created.
**Test:** `tests/integration/test_calendar_engine.py`

### EC-113: Holiday Calendar Conflict Detection [HIGH]
**Scenario:** Event is scheduled on a declared institutional holiday.
**Expected:**
- Validation rejects scheduling or returns a warning depending on configuration.
**Test:** `tests/integration/test_calendar_engine.py`

### EC-114: Faculty Leave Conflict Detection [HIGH]
**Scenario:** Event is scheduled with a faculty member who is on approved leave.
**Expected:**
- Check against leave requests database; rejects event creation or warns scheduler.
**Test:** `tests/integration/test_calendar_engine.py`

### EC-115: Room/Lab Double-Booking Prevention [CRITICAL]
**Scenario:** Attempt to book the same room/lab for overlapping time periods.
**Expected:**
- Reject booking at the database or service validation layer.
**Test:** `tests/integration/test_calendar_engine.py`

### EC-116: Phase Transition Boundary Events [MEDIUM]
**Scenario:** Scheduling events on boundary days (e.g., last day of Phase I overlapping first day of Phase II).
**Expected:**
- Events are strictly bound by the batch's professional phase start/end dates.
**Test:** `tests/integration/test_calendar_engine.py`

### EC-117: Institutional Weekend/Half-day Handling [LOW]
**Scenario:** Events scheduled on Sunday or Saturday afternoon when the institution runs half-days.
**Expected:**
- System alerts scheduler or automatically categorizes attendance accordingly.
**Test:** `tests/integration/test_calendar_engine.py`

### EC-118: Lesson Plan Revision with Existing Sessions [HIGH]
**Scenario:** Faculty creates a new version of a lesson plan while sessions have already been conducted and logged against the previous version.
**Expected:**
- Previous sessions maintain reference to the older immutable lesson plan version record.
- New sessions link to the new current approved version.
**Test:** `tests/integration/test_lesson_plan_service.py`

### EC-119: Unapproved Lesson Plan Session Log [HIGH]
**Scenario:** Session is conducted against a lesson plan that is in 'draft' or 'pending_approval' status.
**Expected:**
- Allowed (to prevent blocking actual classes), but logs a compliance warning or audit log warning.
**Test:** `tests/integration/test_lesson_plan_service.py`

---

## Adding New Edge Cases


When an agent discovers a new edge case during development:

1. Add it to this file with next available ID
2. Document in `docs/AGENT_LEARNINGS.md`
3. Add the corresponding test to `tests/`
4. Update `COVERAGE_MANIFEST.yaml` if it's a manifest-tracked module

**Edge cases are ADDITIVE.** Never remove an edge case unless the scenario is provably impossible.

---

*Total edge cases catalogued: 112 (and growing)*
*All cases have or require corresponding tests in `tests/`*
