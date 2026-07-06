# Session F3 — Logbook + DOAP UI | Session 19 — Phase 3 R0 Planning

> **Both sessions run in parallel. No file conflicts.**
> Frontend (F3): `frontend-web/` | Backend (19): `services/`, `docs/`, `tests/`

---

# FRONTEND: Session F3 — Logbook + DOAP Skills UI

**Agent:** 03-frontend | **Duration:** 4-6 hours
**Goal:** Students create logbook entries and see DOAP progression. Faculty reviews and signs off.

---

## What This Session Delivers

Three new functional pages:

1. **Student Logbook:** Create entry → submit with initials → see status (pending/submitted/approved/rejected)
2. **Faculty Logbook Queue:** See pending submissions → sign off with rating/decision/initials
3. **DOAP Progression:** Visual D→O→A→P pipeline per competency showing current state

---

## Phase A — Types + API Hooks (30 min)

### Type Definitions

Create `src/types/logbook.ts`:

```typescript
export interface LogbookEntry {
  id: string;
  student_id: string;
  subject_code: string | null;
  elective_id: string | null;
  professional_phase: string;
  competency_code: string;
  nmc_level: "K" | "KH" | "SH" | "P";
  is_core: boolean;
  activity_date: string;
  activity_name: string;
  reflection: string | null;
  rating: "B" | "M" | "E" | null;
  faculty_decision: "C" | "R" | "Re" | null;
  faculty_initials: string | null;
  student_initials: string | null;
  status: "pending" | "submitted" | "approved" | "rejected";
  backdated: boolean;
  signed_off_by: string | null;
  signed_off_at: string | null;
  created_at: string;
}

export interface LogbookEntryCreate {
  subject_code?: string;
  elective_id?: string;
  professional_phase: string;
  competency_code: string;
  nmc_level: string;
  is_core: boolean;
  activity_date: string;
  activity_name: string;
  reflection?: string;
}

export interface LogbookSignoff {
  rating: "B" | "M" | "E";
  faculty_decision: "C" | "R" | "Re";
  faculty_initials: string;
  feedback?: string;
}

export interface LogbookSubmit {
  student_initials: string;
}

export interface IAAssessment {
  student_id: string;
  subject_code: string;
  professional_phase: string;
  total_entries: number;
  completed_entries: number;
  ia_marks_pct: number;
  ia_marks_awarded: number;
  is_complete: boolean;
}
```

Create `src/types/doap.ts`:

```typescript
export interface DoapRecord {
  id: string;
  student_id: string;
  competency_code: string;
  stage: "D" | "O" | "A" | "P";
  rating: "B" | "M" | "E";
  attempt_type: "F" | "R" | "Re";
  faculty_decision: "C" | "R" | "Re";
  faculty_id: string;
  signed_off_at: string;
}

export interface DoapState {
  student_id: string;
  competency_code: string;
  current_state: "not_started" | "demonstrated" | "observed" | "assisted" | "performed" | "certified";
  records_per_stage: Record<string, number>;
  certified_stages: string[];
  pending_stage: string | null;
  last_record_at: string | null;
}

export interface DoapProgression {
  student_id: string;
  competency_code: string;
  state: DoapState;
  records: DoapRecord[];
}
```

### API Hooks

Create `src/hooks/use-logbook.ts` and `src/hooks/use-doap.ts` with React Query hooks:

- `useStudentEntries(studentId, filters)` → `GET /logbook/entries?student_id=...`
- `useCreateEntry()` → `POST /logbook/entries`
- `useSubmitEntry()` → `PATCH /logbook/entries/{id}/submit`
- `usePendingSignoffs()` → `GET /logbook/entries?status=submitted` (faculty view)
- `useSignoffEntry()` → `PATCH /logbook/entries/{id}/signoff`
- `useIAAssessment(studentId, subjectCode, phase)` → `GET /logbook/assessments/...`
- `useDoapRecords(studentId, competencyCode?)` → `GET /doap/student/{id}`
- `useDoapState(studentId, competencyCode)` → `GET /doap/student/{id}/competency/{code}/state`

---

## Phase B — Student Logbook Page (90 min)

### B.1 Entry List with Filters

`src/app/(authenticated)/logbook/page.tsx` — role-based routing (same pattern as attendance):

- **Student view:** List of MY entries with status badges + "New Entry" button
- **Faculty view:** Queue of entries pending signoff

### B.2 Create Entry Form

`src/app/(authenticated)/logbook/create-entry-form.tsx`:

- Subject selector (dropdown from student's enrolled courses) OR elective selector
- Competency code input with NMC level selector (K/KH/SH/P)
- Activity date picker (shows backdating warning if > 7 days ago)
- Activity name (text input)
- Reflection (textarea, optional)
- Core/non-core toggle
- Form validation with zod:
  - Either `subject_code` OR `elective_id` required (not both, not neither)
  - `activity_date` cannot be in the future
  - `competency_code` required, min 2 chars

### B.3 Entry Status Flow

Show entries in a table/card list with clear status indicators:

```
Status badges:
  pending    → gray "Draft"
  submitted  → blue "Submitted" (with student initials shown)
  approved   → green "Approved ✓" (with faculty initials + decision)
  rejected   → red "Needs Revision" (with faculty feedback)
```

### B.4 Submit Entry Dialog

When student clicks "Submit" on a pending entry:
- Dialog asks for student initials (required, LOG-NMC-010 compliance)
- On confirm → calls `PATCH /logbook/entries/{id}/submit`
- Status changes to "submitted"

---

## Phase C — Faculty Signoff Queue (60 min)

### C.1 Pending Queue

`src/app/(authenticated)/logbook/faculty-queue.tsx`:

- Table of all entries with `status=submitted` for the faculty's courses
- Columns: Student Name, Subject, Competency, Activity Date, Activity Name
- Click row → opens signoff sheet

### C.2 Signoff Sheet

`src/app/(authenticated)/logbook/signoff-sheet.tsx`:

Slide-out panel showing:
- Entry details (read-only: student name, subject, competency, activity, reflection)
- **Rating selector:** B (Below) / M (Meets) / E (Exceeds) — radio buttons
- **Decision selector:** C (Certify) / R (Repeat) / Re (Remediate) — radio buttons
- **Validation:** Rating B + Decision C is BLOCKED (shows inline error, submit button disabled)
- **Faculty initials:** required text input (LOG-NMC-009 compliance)
- **Feedback:** optional textarea
- Submit button: "Certify" (green) or "Request Revision" (amber) based on decision

### C.3 IA Summary Card

Show IA marks summary at the top of student's logbook view:

```
┌─────────────────────────────────────────────┐
│ Internal Assessment — Anatomy (Phase I)      │
│                                              │
│ Entries: 7/10 completed                      │
│ IA Weight: 10%                               │
│ IA Marks: 2.80 / 4.00                        │
│ ████████████████████░░░░░  70%               │
└─────────────────────────────────────────────┘
```

---

## Phase D — DOAP Progression View (60 min)

This is the most visually distinctive page in the application.

### D.1 Competency List

`src/app/(authenticated)/doap/page.tsx`:

- Student: list of all competencies they've attempted, grouped by subject
- Faculty: list of students they supervise, expandable to see competencies

### D.2 D→O→A→P Pipeline

`src/app/(authenticated)/doap/doap-pipeline.tsx`:

Visual pipeline showing four stages as connected nodes:

```
  ┌───┐    ┌───┐    ┌───┐    ┌───┐
  │ D │───→│ O │───→│ A │───→│ P │
  └───┘    └───┘    └───┘    └───┘
   ✓ 2      ✓ 1      ● 0      ○ 0
  Certified Certified Current  Locked
```

Implementation:
```typescript
const STAGES = ["D", "O", "A", "P"] as const;
const STAGE_LABELS = { D: "Demonstration", O: "Observation", A: "Assistance", P: "Performance" };
const STAGE_COLORS = {
  certified: "bg-green-500 text-white",      // Has C decision
  current: "bg-blue-500 text-white",          // Next stage to attempt
  locked: "bg-zinc-200 text-zinc-400",        // Can't attempt yet
};

function DoapPipeline({ state }: { state: DoapState }) {
  return (
    <div className="flex items-center gap-2">
      {STAGES.map((stage, i) => {
        const isCertified = state.certified_stages.includes(stage);
        const isCurrent = state.pending_stage === stage;
        const count = state.records_per_stage[stage] || 0;
        const colorClass = isCertified
          ? STAGE_COLORS.certified
          : isCurrent
            ? STAGE_COLORS.current
            : STAGE_COLORS.locked;

        return (
          <Fragment key={stage}>
            {i > 0 && <div className="h-0.5 w-8 bg-zinc-300" />}
            <div className="text-center">
              <div className={`h-10 w-10 rounded-full flex items-center justify-center text-sm font-bold ${colorClass}`}>
                {stage}
              </div>
              <p className="text-xs mt-1 text-muted-foreground">{count} records</p>
              <p className="text-xs font-medium">
                {isCertified ? "✓ Certified" : isCurrent ? "● Current" : "○ Locked"}
              </p>
            </div>
          </Fragment>
        );
      })}
    </div>
  );
}
```

### D.3 Stage Detail View

Clicking a stage shows all records for that stage:
- Date, faculty name, rating, decision, attempt type
- Colour coded: C=green, R=amber, Re=red

---

## Phase E — Verification + Commit (15 min)

Manual testing checklist:

- [ ] Student creates logbook entry (regular + elective)
- [ ] Backdating > 7 days shows warning badge
- [ ] Student submits with initials
- [ ] Faculty sees submitted entries in queue
- [ ] Faculty signs off with rating B + decision C → blocked by validation
- [ ] Faculty signs off with rating M + decision C → approved, green badge
- [ ] Faculty signs off with decision R → rejected, "Needs Revision" badge
- [ ] IA summary card shows correct calculation
- [ ] DOAP pipeline shows correct stage states
- [ ] DOAP pipeline: certified stages green, current blue, locked gray
- [ ] Mobile responsive: all pages work on narrow viewport

Screenshots saved to `docs/screenshots/session-f3/`.

Commit:
```
feat(frontend): Session F3 — Logbook + DOAP Skills UI

- Student logbook: create entry, submit with initials, view status
- Faculty logbook: pending queue, signoff sheet with rating/decision validation
- IA marks summary card with progress bar
- DOAP D→O→A→P visual pipeline per competency
- Stage detail view with colour-coded decisions
- Rating B + Decision C validation enforced in UI
- React Query hooks for logbook + DOAP endpoints
```

---
---

# BACKEND: Session 19 — Phase 3 R0: Examination Management Planning

**Agent:** 02-backend (or 00-orchestrator for planning)
**Duration:** 4-5 hours
**Goal:** Complete R0 for Phase 3. No code — documentation, ADRs, schema spec, test categorisation only.

---

## Why R0 First

You know the pattern now. R0 produces:
1. ADRs for all Phase 3 architectural decisions
2. PHASE3_SCHEMA.md with complete table definitions
3. COVERAGE_MANIFEST additions with test IDs
4. Test categorisation (must-pass vs deferred)
5. Verifier baselines

This was the discipline that made Phase 2 successful. Apply it identically to Phase 3.

---

## Phase A — Phase 3 ADRs (90 min)

Create ADRs 038-048 in `docs/DECISIONS.md`:

### ADR-038: IA Aggregation Formula

**Decision:** Internal Assessment marks aggregate from multiple sources:
- Logbook completion (already implemented, ia_marks_awarded)
- Periodic viva scores (new table: `viva_scores`)
- Practical exam scores (new table: `practical_assessments`)
- Clinical posting evaluation (new table: `clinical_evaluations`)

Final IA = weighted sum per NMC regulation:
```
total_ia = (logbook_ia × logbook_weight) + (viva_ia × viva_weight) + 
           (practical_ia × practical_weight) + (clinical_ia × clinical_weight)
```

Weights configurable per subject via MDM. Default: 20% logbook, 30% viva, 30% practical, 20% clinical.

### ADR-039: Exam Eligibility Engine

**Decision:** Student exam eligibility requires ALL of:
1. Attendance ≥ threshold per category (from Phase 2)
2. Logbook completion = TRUE for the subject (from Phase 2)
3. IA total ≥ minimum (configurable, default 50% of IA max)
4. No active disciplinary suspension
5. All prerequisite subjects passed (for Phase II+ subjects)

Returns: `{ eligible: bool, blocking_reasons: [{ code, message, resolution }] }`

### ADR-040: Grade Calculation (NMC Scheme)

**Decision:** NMC grading:
- ≥ 75%: Distinction
- 50-74%: Pass
- < 50%: Fail

Applied separately to theory AND practical. Must pass BOTH independently.
Grace marks: maximum 5 marks total per examination, configurable via MDM.

### ADR-041: Supplementary Exam Rules

**Decision:**
- Maximum 4 supplementary attempts per subject (NMC regulation)
- Grace marks NOT applicable in supplementary exams
- Previous attempt marks retained as history (not overwritten)
- Student status: regular → supplementary → detained (if 4 attempts exhausted)

### ADR-042: Mark Sheet Generation

**Decision:** PDF generation using WeasyPrint (already in stack). Template-based:
- HTML template with CSS for print layout
- Dynamic data injection from exam_results
- QR code with verification URL
- Digital signature placeholder (Phase 4 for actual implementation)
- Output stored as digital_asset

### ADR-043: Exam Scheduling Conflict Prevention

**Decision:**
- Same student cannot have two exams at same time
- Same room cannot host two exams at same time
- Minimum 1-day gap between theory exams for same student (configurable)
- Practical exams can be same-day as theory (different time)

### ADR-044: Question Paper Versioning

**Decision:** Question papers stored as digital_assets with:
- Version tracking (draft → submitted → approved → locked)
- Access control: only exam controller can view before exam
- Audit log for every access
- Post-exam: automatically made accessible for review

### ADR-045: Result Processing Workflow

**Decision:** Workflow engine (existing) used for result processing:
- Examiner submits marks → HOD verifies → Principal approves → Results published
- Each step is a workflow_transition
- Results not visible to students until workflow reaches "published" state

### ADR-046: External Exam Integration

**Decision:** University exam results imported via CSV. Mapping:
- Student matched by enrollment number
- Subject matched by subject code
- Marks validated against schema (0-max range)
- Duplicate detection by (student, subject, exam_session)

### ADR-047: Exam Analytics Views

**Decision:** Materialised views for:
- Pass percentage per subject per batch
- Average marks trend (semester over semester)
- At-risk student identification (failed 2+ subjects)
- Faculty effectiveness correlation (teaching → results)

### ADR-048: Multi-Examiner Moderation

**Decision:** For subjects with multiple examiners:
- Moderation formula: final = average of all examiners if within 15% range
- If gap > 15%: third examiner mandatory
- Stored in `exam_moderation` table with all examiner marks and final computed mark

---

## Phase B — Phase 3 Schema (60 min)

Create `docs/PHASE3_SCHEMA.md` with DDL for:

```sql
-- Core exam tables
examinations (id, tenant_id, curriculum_id, course_id, exam_type, exam_session,
              academic_year, exam_date, theory_max_marks, practical_max_marks,
              theory_pass_marks, practical_pass_marks, grace_marks_allowed,
              status ['scheduled','in_progress','completed','results_published'],
              workflow_instance_id, ...)

exam_schedules (id, tenant_id, examination_id, room_id, 
                start_time, end_time, invigilator_id, ...)

-- IA aggregation (extends Phase 2)
viva_scores (id, tenant_id, student_id, course_id, professional_phase,
             examiner_id, marks_obtained, max_marks, conducted_at, ...)

practical_assessments (id, tenant_id, student_id, course_id, professional_phase,
                       examiner_id, marks_obtained, max_marks, conducted_at, ...)

clinical_evaluations (id, tenant_id, student_id, course_id, professional_phase,
                      evaluator_id, marks_obtained, max_marks, posting_period, ...)

ia_aggregation (tenant_id, student_id, course_id, professional_phase,
                logbook_marks, viva_marks, practical_marks, clinical_marks,
                total_ia, ia_max, is_eligible,
                PRIMARY KEY (tenant_id, student_id, course_id, professional_phase))

-- Exam eligibility
exam_eligibility (tenant_id, student_id, examination_id,
                  is_eligible, blocking_reasons JSONB,
                  checked_at, checked_by,
                  PRIMARY KEY (tenant_id, student_id, examination_id))

-- Results
exam_results (id, tenant_id, student_id, examination_id,
              theory_marks, practical_marks, ia_marks, total_marks,
              theory_grade, practical_grade, overall_grade,
              grace_marks_applied, attempt_number,
              status ['draft','verified','approved','published'],
              workflow_instance_id, ...)

exam_moderation (id, tenant_id, exam_result_id,
                 examiner_1_marks, examiner_2_marks, examiner_3_marks,
                 moderation_method, final_marks, ...)

-- Mark sheets
mark_sheets (id, tenant_id, student_id, academic_year, semester,
             pdf_asset_id, qr_verification_code, generated_at,
             generated_by, ...)

-- Question papers
question_papers (id, tenant_id, examination_id,
                 paper_type ['theory','practical','viva'],
                 version, asset_id, status ['draft','approved','locked'],
                 ...)
```

Cross-reference against existing Phase 2 tables to identify:
- FKs to existing tables (students, courses, curricula, faculty, digital_assets, workflow_instances)
- New unique constraints needed on existing tables

---

## Phase C — Coverage Manifest + Test Categorisation (60 min)

Add Phase 3 test IDs to `tests/COVERAGE_MANIFEST.yaml`:

Estimated ~60 test IDs across:
- `exam_management` (EXM-001..020): scheduling, conflicts, lifecycle
- `ia_aggregation` (IA-001..010): multi-source aggregation, weight calculation
- `exam_eligibility` (ELIG-001..010): eligibility engine, blocking reasons
- `exam_results` (RES-001..010): grading, moderation, publication workflow
- `mark_sheets` (MKS-001..005): PDF generation, QR codes
- Compliance tests (EXM-NMC-001..010): pass marks, grace marks, attempt limits

Create `docs/verification/phase3_test_categorisation.md`:
- Must pass Phase 3: ~45 tests
- Deferred to Phase 3.5: ~10 tests (analytics views, question paper management)
- Deferred to Phase 4: ~5 tests (digital signatures, university integration)

Capture verifier baseline:
```powershell
python scripts/verify_coverage_manifest.py 2>&1 | Tee-Object docs/verification/phase3_baseline_$(Get-Date -Format yyyyMMdd).txt
```

---

## Phase D — Verification + Handoff (15 min)

```powershell
python scripts/verify_adr_sequence.py
# Expected: ADR-001 through ADR-048, no gaps
```

Commit:
```
docs: Session 19 — Phase 3 R0 Examination Management planning

- ADRs 038-048 (IA aggregation, eligibility engine, grading, supplementary,
  mark sheets, scheduling, question papers, result workflow, external import,
  analytics, multi-examiner moderation)
- docs/PHASE3_SCHEMA.md with 10 new tables
- COVERAGE_MANIFEST Phase 3 additions (~60 test IDs)
- Phase 3 test categorisation and verifier baseline

Phase 3 R0 complete. R1-R3 (schema + stubs + migrations) next.
```

---

## After Both Sessions

| Track | Completed | What you can do |
|---|---|---|
| Frontend | F3 done | Students create logbook entries, faculty signs off, DOAP pipeline visible |
| Backend | Phase 3 R0 done | Examination Management fully planned, 48 ADRs, schema specified |

**Next parallel pair:**
- **Session F4:** Electives + Leave UI (preference ranking, allocation view, leave requests)
- **Session 20-21:** Phase 3 R1-R3 (exam schema finalisation + test stubs + migrations)