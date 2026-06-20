# Synaptix — Master Specification v5.0
## Academic Operations & Intelligence Platform — Definitive Product Spec

> **This is the definitive specification.** Earlier versions (v1.0 through v4.0) are superseded.
> All agents read relevant sections of this file at the start of every session.

**Owner:** Nirmala Foundation
**Product code:** SNX
**Primary institution:** JMN Medical College & Hospital, Kalyani, Nadia, West Bengal
**Version:** 5.0
**Date:** 2026-06-18
**Supersedes:** v1.0, v2.0, v3.0, v4.0, all audits, all feasibility analyses

---

## How To Use This Document

This document is organised in three layers:

- **Layer 1: WHAT** — what we are building (Sections 1–6)
- **Layer 2: HOW** — how we are building it (Sections 7–14)
- **Layer 3: WHEN & WHY** — phasing, rationale, edge cases (Sections 15–20)

For quick lookups:
- Module list: §5
- Database schema: §7
- NMC compliance rules: §11
- Edge cases: §18
- Delivery phases: §17

---

## Table of Contents

### Layer 1: WHAT We're Building
1. [Product Vision & Design Principles](#1-product-vision)
2. [Multi-Tenant Scope & Hierarchy](#2-multi-tenant-scope)
3. [Curriculum Models (CBME 2019 & 2023)](#3-curriculum-models)
4. [User Roles & Permissions](#4-user-roles)
5. [Module Catalogue (49 Modules, 7 Layers)](#5-module-catalogue)
6. [User Journeys](#6-user-journeys)

### Layer 2: HOW We're Building It
7. [Database Schema](#7-database-schema)
8. [API Design](#8-api-design)
9. [Service Architecture (12 Grouped Services)](#9-service-architecture)
10. [Cloud Infrastructure (3 Tiers)](#10-cloud-infrastructure)
11. [NMC Compliance Engine](#11-nmc-compliance-engine)
12. [Offline-First Mobile Strategy](#12-offline-first-mobile)
13. [AI Layer](#13-ai-layer)
14. [Security & DPDP Act 2023 Compliance](#14-security-dpdp)

### Layer 3: WHEN & WHY
15. [Solo Developer + Agent Framework](#15-solo-developer-agent-framework)
16. [Testing Strategy](#16-testing-strategy)
17. [Delivery Phases](#17-delivery-phases)
18. [Edge Cases Catalogue](#18-edge-cases-catalogue)
19. [Risk Register](#19-risk-register)
20. [Open Decisions](#20-open-decisions)

---

# Layer 1: WHAT We're Building

## 1. Product Vision

Synaptix is a **Unified Academic Operations & Intelligence Platform** serving as the operational backbone for medical colleges, nursing colleges, allied health institutions, pharmacy colleges, engineering colleges, universities, and schools.

It evolves into a **Digital Twin of the Institution** where every academic, clinical, research, administrative, and student activity is represented in real time, enabling data-driven operations, predictive insights, accreditation readiness, and AI-assisted decision-making.

### Core Design Principles

1. **Configurable, not hardcoded** — every institution-specific element is configurable. However, NMC-mandated rules (75% theory, 80% practical attendance, logbook prerequisite, competency completion) are enforced at the engine level with Principal-level exemption and audit trail.

2. **Multi-tenant from day one** — single deployment, strict data isolation, super-admin aggregate analytics.

3. **Offline-first for Indian conditions** — attendance, logbook, and session tracking work without internet.

4. **Compliance built in** — NMC CBME 2019/2023, NAAC, INC, NBA, UGC, DPDP Act 2023 rules are enforced at the engine level, not bolted on as reports.

5. **AI ready** — every activity is stored as a structured event so the AI layer can query, analyse, and predict.

6. **Evidence-first** — every metric auto-links to its evidence chain for instant accreditation readiness.

7. **Cost-conscious scaling** — start minimal, scale only when triggered by real demand.

8. **Agent-buildable** — the system architecture allows AI agents to build modules in parallel without breaking each other's work.

## 2. Multi-Tenant Scope

### Tenant Hierarchy

```
Nirmala Foundation (Super Admin)
├── JMN Medical College (PRIMARY — Year 1 launch)
├── IINR (Institute of Nursing)
├── IIHMAHS (Allied Health Sciences)
├── IIPSR (Pharmacy)
├── CCNR (Nursing)
├── ICHFN (Nursing)
├── Nirmala Vishwa Vidyapeeth (future university)
└── Future schools
```

Each institution is a **tenant** with strict data isolation. Multi-tenancy is enforced at three layers:

1. **API Gateway** — extracts `tenant_id` from JWT, injects into request context
2. **Middleware** — applies `tenant_id` filter to every database query automatically
3. **PostgreSQL Row Level Security** — second-layer enforcement that no service can bypass

### Tenant Onboarding Automation

When a new tenant is added:
- MDM seed data loaded from template (departments, designations, leave types, exam types)
- Default workflows provisioned (leave, lesson plan, result moderation)
- Role templates with standard RBAC
- Regulatory rule set loaded (NMC for medical, INC for nursing, etc.)
- Empty academic structure ready for population
- Branding configured (logo, colours, name)

This is a **self-service admin workflow** — no engineering required to add a new institution.

## 3. Curriculum Models

Synaptix supports two models simultaneously:

### Model A: Professional Phase (MBBS — NMC mandated)

```
Institution → Academic Year → Program: MBBS → Curriculum
    │
    ├── NMC CBME 2019 (for JMN 2023 admission batch — currently in Phase II)
    │   └── Phase I (12mo) → Phase II (12mo) → Phase III Part I (12mo) → Phase III Part II (12mo)
    │
    └── NMC CBME 2023 (for JMN 2024 admission batch onwards)
        └── Phase I (12mo) → Phase II (12mo) → Phase III Part I (12mo) → Phase III Part II (12mo)
            + Foundation Course (1 month at Phase I start)
            + AETCOM (longitudinal across all phases)
            + ECE (Phase I)
            + Electives Block 1 & 2 (2×4 weeks after Phase III Part I exam)
            + CRMI (12 months post-degree)
```

### Model B: Semester (Nursing, Allied Health, Pharmacy, Engineering, University)

```
Institution → Academic Year → Program → Curriculum → Semester → Course → Batch
```

The system detects the calendar model from program configuration and renders UI, attendance rules, and hall ticket eligibility logic accordingly.

### JMN Batch Status (as of June 2026)

| Admission Year | Batch | Curriculum | Current Status |
|---------------|-------|-----------|----------------|
| 2023 | MBBS-2023 | NMC CBME 2019 | Phase II |
| 2024 | MBBS-2024 | NMC CBME 2023 | Phase I |
| 2025 | MBBS-2025 | NMC CBME 2023 | Phase I (recently admitted) |
| 2026 | MBBS-2026 | NMC CBME 2023 | Pre-admission |

## 4. User Roles

| Role | Scope | Key Capabilities |
|------|-------|------------------|
| `super_admin` | All tenants | Full platform, tenant management, billing |
| `institution_admin` | One institution | All modules for that institution |
| `principal` | One institution | Governance, compliance reports, exemption grants |
| `dean` | One institution | Academic governance |
| `controller_of_examinations` | One institution | Exam scheduling, result moderation, hall tickets |
| `hod` | One department | Department timetable, faculty load, student reports |
| `faculty` | Own subjects | Lesson plans, sessions, attendance, marks, logbook sign-off |
| `curriculum_committee_member` | Program-level | Curriculum governance, integration planning |
| `meu_faculty` | Institution-level | Assessment design oversight, faculty development |
| `mentor` | Assigned students | Student monitoring, counselling |
| `student` | Own data | Timetable, attendance, results, leave, logbook, portfolio |
| `intern` | Own internship | Rotation, logbook, duty roster |
| `parent` | Child's data | Read-only: attendance, results, fee dues |
| `accreditation_officer` | Reports only | NMC, NAAC, INC report generation |
| `alumni` | Own profile | Career updates, mentorship |
| `inspector` | Time-limited, read-only | NMC/NAAC inspection access |

### Authentication Methods

- Google SSO
- Microsoft SSO
- Email + password
- OTP (mobile number)
- WhatsApp OTP

### Authorization Model

RBAC + ABAC. RBAC for role-level permissions, ABAC for attribute-based filtering (e.g., faculty only sees their own students).

MFA required for: `admin`, `principal`, `dean`, `controller_of_examinations`.

## 5. Module Catalogue

Synaptix has **49 modules across 7 layers**. For Year 1, all are scaffolded; production-grade implementation follows the phase plan in §17.

### Layer 1: Foundation (7 modules)

| ID | Module | Phase | Priority |
|----|--------|-------|----------|
| F-01 | Identity & Access Management | 1A | Critical |
| F-02 | Master Data Management (MDM) | 1A | Critical |
| F-03 | Workflow Engine | 1A | Critical |
| F-04 | Notification Centre | 2 | High |
| F-05 | WhatsApp Bot | 2 | High |
| F-06 | Document Generation | 3 | High |
| F-07 | Digital Asset Repository | 5 | Medium |

### Layer 2: Academic (16 modules)

| ID | Module | Phase | Priority |
|----|--------|-------|----------|
| A-01 | Academic Structure Engine | 1A | Critical |
| A-02 | Curriculum Version Migration Engine | 1B | Critical |
| A-03 | Timetable Scheduler | 1A | Critical |
| A-04 | Academic Calendar Engine | 1B | Critical |
| A-05 | Lesson Plan Engine | 1B | High |
| A-06 | Session Tracking | 1B | High |
| A-07 | Foundation Course & AETCOM | 1B | Critical |
| A-08 | Electives | 2 | Critical |
| A-09 | Skills Lab & DOAP | 2 | High |
| A-10 | Digital Logbook & Portfolio | 2 | Critical |
| A-11 | Attendance Engine (two-threshold) | 2 | Critical |
| A-12 | Leave Management | 2 | High |
| A-13 | Examination Management | 3 | Critical |
| A-14 | Result Management | 3 | Critical |
| A-15 | Outcome-Based Education (OBE) | 3 | High |
| A-16 | LMS (basic, with Google Classroom integration) | 5 | Low |

### Layer 3: Medical Education (4 modules)

| ID | Module | Phase | Priority |
|----|--------|-------|----------|
| M-01 | Clinical Management | 4 | Critical |
| M-02 | Competency-Based Education (CBE) | 4 | Critical |
| M-03 | Internship / CRMI Management | 4 | Critical |
| M-04 | Hospital Integration Layer (HIMS, EMR, LIS, PACS) | 4 | Very High |

### Layer 4: Institution (16 modules)

| ID | Module | Phase | Priority |
|----|--------|-------|----------|
| I-01 | Student Lifecycle Management | 1A | High |
| I-02 | Admission Module | 2 | High |
| I-03 | Student Success Centre | 4 | High |
| I-04 | Faculty Management (with Curriculum Committee + MEU) | 3 | High |
| I-05 | Research Management | 5 | High |
| I-06 | Accreditation & Compliance | 5 | Critical |
| I-07 | Accreditation Evidence Locker | 5 | Very High |
| I-08 | IQAC Module | 5 | High |
| I-09 | Outreach Management (Family Adoption Programme) | 4 | Medium |
| I-10 | Resource & Asset Management | 3 | High |
| I-11 | Hostel Management | 6 | Medium |
| I-12 | Institution Command Center | 5 | Very High |
| I-13 | Placement & Career Services | 6 | Medium |
| I-14 | Alumni Engagement | 6 | Medium |
| I-15 | Conference & Event Management | 6 | Low |
| I-16 | Transport & Fleet Management | 6 | Low |

### Layer 5: Intelligence (5 modules)

| ID | Module | Phase | Priority |
|----|--------|-------|----------|
| X-01 | Analytics & Business Intelligence | 5 | High |
| X-02 | Analytics Data Warehouse (BigQuery pipeline) | 5 | High |
| X-03 | AI Academic Assistant | 6 | High |
| X-04 | AI Copilots (Faculty, Student, Management) | 6 | High |
| X-05 | Predictive Analytics Engine | 6 | High |

### Layer 6: Integration (4 modules)

| ID | Module | Phase | Priority |
|----|--------|-------|----------|
| N-01 | Hospital Integration APIs (HIMS already exists at JMN) | 4 | Very High |
| N-02 | Fee Portal Integration Hook (existing fees portal) | 5 | High |
| N-03 | API Marketplace | 6 | Medium |
| N-04 | External LMS Integration (Google Classroom) | 5 | Low |

### Layer 7: Infrastructure (3 modules)

| ID | Module | Phase | Priority |
|----|--------|-------|----------|
| Z-01 | Enhanced Security Layer (MFA, SIEM, PAM) | 1A | Critical |
| Z-02 | Monitoring & Observability | 1A | Critical |
| Z-03 | Disaster Recovery | 2 | Critical |

## 6. User Journeys

These are the canonical user journeys that drive the design. Every test in `tests/e2e/` corresponds to one of these.

### J-01: Student daily flow
1. Student opens mobile app at 8:00 AM
2. Sees today's timetable
3. Faculty scans QR for first lecture
4. Student's phone auto-marks attendance (offline-capable)
5. Between classes, student opens AETCOM module, completes a reflection
6. After lab session, student adds a logbook entry for DOAP skill practised
7. Phone syncs when WiFi is available
8. Evening: student checks portfolio, adds today's logbook entry to portfolio

### J-02: Faculty teaching flow
1. Faculty opens web app at start of day
2. Views teaching schedule
3. Generates session QR code before each class
4. After class: marks attendance corrections (if any), records topics covered
5. Signs off student logbook entries from clinical posting
6. Submits lesson plan for next week to HOD for approval

### J-03: HOD oversight flow
1. HOD opens dashboard
2. Sees department-wide attendance heatmap
3. Identifies at-risk students (below 80% practical attendance)
4. Approves pending lesson plans
5. Reviews faculty teaching load distribution

### J-04: Dean / Principal governance flow
1. Opens Institution Command Center
2. Sees Institution Health Score
3. Drills down into compliance gaps
4. Generates NMC inspection-ready report
5. Reviews exemption requests from students with attendance shortfall

### J-05: NMC inspector flow (read-only)
1. Inspector arrives with appointment
2. Principal creates inspector account with 7-day expiry
3. Inspector logs in with OTP
4. Accesses pre-built NMC inspection pack
5. Queries specific data: faculty list, attendance registers, logbook completion, research output
6. All access logged in audit trail
7. Account auto-deactivates after 7 days

### J-06: NExT eligibility check (Phase III Part II student)
1. Student opens "NExT eligibility" page
2. System runs eligibility check:
   - Theory attendance ≥ 75% per subject (all phases)
   - Practical attendance ≥ 80% per subject (all phases)
   - Elective Block 1 attendance ≥ 75% + logbook submitted
   - Elective Block 2 attendance ≥ 75% + logbook submitted
   - MBBS logbook submitted and assessed for all phases
   - AETCOM completed per phase
   - Certified skills signed off
   - Minimum IA tests completed per subject
   - Fee clearance
3. Result: ELIGIBLE or NOT ELIGIBLE with specific failure reasons
4. If ineligible, Principal can grant exemption (audit logged)

### J-07: Intern CRMI flow
1. Intern starts CRMI rotation in General Medicine
2. Daily duty roster shown
3. Marks attendance per duty day
4. Records logbook entries (cases, procedures)
5. After 2 months: end-of-rotation assessment by supervisor
6. Moves to next mandatory rotation
7. After 12 months: CRMI Completion Certificate generated (if all rotations satisfactorily completed)

---

# Layer 2: HOW We're Building It

## 7. Database Schema

The complete schema is in `scripts/seed-nmc-data.sql`. Below is the structural summary.

### Multi-Tenancy Pattern

Every tenant-scoped table includes:
```sql
tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

And has a Row Level Security policy:
```sql
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_{table} ON {table}
    USING (tenant_id = current_setting('snx.current_tenant_id')::UUID);
```

### Table Catalogue (40+ core tables)

**Foundation Layer:**
- `tenants`, `institutions`, `users`, `roles`, `permissions`, `user_roles`
- `master_data_entities`, `workflow_definitions`, `workflow_instances`
- `notification_log`, `audit_log`, `digital_assets`

**Academic Layer:**
- `academic_years`, `programs`, `curricula`, `courses`, `batches`, `sections`
- `students`, `faculty`, `departments`
- `events` (central calendar), `lesson_plans`, `sessions`
- `attendance`, `attendance_summary` (materialised), `leave_requests`
- `assessments`, `results`, `competencies`
- `foundation_course_records`, `aetcom_records`
- `electives`, `elective_allocations`, `elective_logbook_entries`
- `doap_session_records`, `logbook_entries`, `logbook_assessments`, `portfolio_entries`

**Medical Education Layer:**
- `clinical_postings`, `clinical_logbook_entries`
- `internship_rotations`, `intern_attendance`, `intern_logbook_entries`, `intern_duty_roster`
- `crmi_leave_tracker`

**Institution Layer:**
- `student_lifecycle_states`, `admission_applications`
- `resources`, `resource_bookings`, `assets`
- `evidence_records`, `iqac_action_items`, `iqac_feedback`
- `command_center_snapshots`, `alumni_profiles`
- `curriculum_committee_records`, `meu_programmes`

**Edge Case Tables (from audit):**
- `transfer_in_records`, `detention_records`
- `attendance_accommodations`, `emergency_overrides`
- `inspector_access`, `exam_invalidations`
- `next_eligibility`

See `scripts/seed-nmc-data.sql` for complete DDL with indexes, constraints, and seed data.

### Critical Indexes

```sql
-- Attendance percentage queries (most frequent)
CREATE INDEX idx_attendance_student_subject_category
    ON attendance(student_id, attendance_category, phase);

-- Event lookup by batch/date
CREATE INDEX idx_events_batch_date
    ON events(batch_id, date);

-- Audit trail queries
CREATE INDEX idx_audit_log_tenant_resource
    ON audit_log(tenant_id, resource_type, resource_id);

-- Logbook completion queries
CREATE INDEX idx_logbook_student_phase_subject
    ON logbook_entries(student_id, professional_phase, subject_code);
```

### Partitioning Strategy

`attendance` and `audit_log` tables are partitioned by `academic_year_id` (range partitioning) to handle the projected 100M+ rows over 5 years.

## 8. API Design

### URL Versioning

All APIs are versioned in URL: `/api/v1/...`. Breaking changes require new version (`v2`). Old versions supported for 12 months with deprecation warnings.

### Response Envelope

Every API response uses this envelope:

```json
{
  "success": true,
  "data": { /* response data */ },
  "meta": {
    "timezone": "Asia/Kolkata",
    "request_id": "uuid",
    "api_version": "v1"
  },
  "errors": null
}
```

On error:

```json
{
  "success": false,
  "data": null,
  "meta": { "request_id": "uuid", "api_version": "v1" },
  "errors": [
    {
      "code": "SNX-ATT-001",
      "message": "Theory attendance below 75% threshold",
      "field": "attendance_pct_theory",
      "details": { "current": 73.5, "required": 75.0 }
    }
  ]
}
```

### Authentication

JWT bearer tokens. Token contains: `user_id`, `tenant_id`, `roles[]`, `expires_at`. Refresh tokens for long sessions.

### Rate Limiting

- Public endpoints: 60 req/min per IP
- Authenticated endpoints: 600 req/min per user
- Admin endpoints: 1200 req/min per user
- AI endpoints: 30 req/min per user (cost-sensitive)

See `conventions/API_DESIGN.md` for complete specification.

## 9. Service Architecture

**12 grouped services** (instead of 49 microservices) for operational sanity:

| Service | Modules Contained | Port (Local) |
|---------|-------------------|--------------|
| `snx-auth` | F-01 Identity & Access | 8001 |
| `snx-academic` | A-01 to A-06 (Academic structure, calendar, lesson plans) | 8002 |
| `snx-attendance` | A-11 Attendance, A-12 Leave | 8003 |
| `snx-exam` | A-13 Exam, A-14 Result, A-15 OBE | 8004 |
| `snx-clinical` | M-01 to M-03 (Clinical, CBE, CRMI) | 8005 |
| `snx-logbook` | A-07 Foundation/AETCOM, A-08 Electives, A-09 DOAP, A-10 Logbook | 8006 |
| `snx-institution` | I-01 to I-04, I-10 (Lifecycle, Admissions, Success, Faculty, Resources) | 8007 |
| `snx-compliance` | I-05 to I-08, I-09 (Research, Accreditation, Evidence, IQAC, Outreach) | 8008 |
| `snx-notification` | F-04 Notification, F-05 WhatsApp Bot, F-06 Documents | 8009 |
| `snx-workflow` | F-02 MDM, F-03 Workflow Engine, F-07 Digital Assets | 8010 |
| `snx-analytics` | X-01 Analytics, X-02 Warehouse, I-12 Command Center | 8011 |
| `snx-ai` | X-03 AI Assistant, X-04 Copilots, X-05 Predictive | 8012 |

Each service is a FastAPI application with multiple routers (one per module). Services communicate via Pub/Sub events (async) and HTTP (sync).

## 10. Cloud Infrastructure

### Three Tiers with Scale-Up Triggers

**Tier 0: Local Development (₹0/month)**
- PostgreSQL via Docker Compose
- Services run via `uvicorn --reload`
- In-process events (no Pub/Sub)
- No cloud needed

**Tier 1: MVP (₹25,000–43,000/month)**
- Cloud Run (scale-to-zero) for all 12 services
- Cloud SQL PostgreSQL single instance
- Cloud Storage (Autoclass)
- Pub/Sub
- No Redis (sessions in DB)
- No BigQuery (analytics against read replica when added)

**Triggers Tier 1 → Tier 2:**
- Consistent 500+ concurrent users
- Second institution goes live
- Dashboard slow under load
- First NMC/NAAC inspection approaching

**Tier 2: Growth (₹93,000–1,60,000/month)**
- Cloud Run with min instances OR GKE Autopilot
- Cloud SQL HA + Read Replica + DR Replica
- Redis Memorystore
- Elasticsearch
- BigQuery CDC pipeline

**Triggers Tier 2 → Tier 3:**
- 1000+ concurrent users sustained
- AI features go live
- 5+ institutions live
- ML training pipelines needed

**Tier 3: Enterprise (₹1,72,000–3,21,000/month)**
- GKE Autopilot
- Full Cloud SQL HA with replicas
- Redis HA
- Elasticsearch cluster
- Full BigQuery warehouse
- Vertex AI training + serving

### Region Strategy

- Primary: asia-south1 (Mumbai)
- DR: asia-south2 (Delhi)
- Data residency: India only (DPDP Act compliance)

## 11. NMC Compliance Engine

### The Two-Threshold Rule (NON-NEGOTIABLE for MBBS)

| Category | Minimum | Alert | Block |
|----------|---------|-------|-------|
| Theory | **75%** | 80% | 75% |
| Practical / Clinical / DOAP / ECE | **80%** | 85% | 80% |
| Electives (Block 1 & Block 2) | **75%** | 80% | 75% |
| AETCOM | **75%** | 80% | 75% |
| Foundation Course | Track separately | — | Certificate withheld |

### Hall Ticket / NExT Eligibility

A student qualifies for hall ticket / NExT only if ALL of the following are true:

1. Theory attendance ≥ 75% in every subject (current phase)
2. Practical attendance ≥ 80% in every subject (current phase)
3. Logbook submitted AND assessed for current phase
4. Minimum IA tests completed per subject
5. AETCOM IA completed for current phase
6. Certifiable competencies signed off
7. Fee status clear

**Additional for NExT specifically:**
8. Electives Block 1 attendance ≥ 75% + logbook submitted
9. Electives Block 2 attendance ≥ 75% + logbook submitted

If any check fails, Principal can grant exemption with audit-logged reason.

### NMC CBME Competency Taxonomy

| Level | Code | Meaning | Assessment |
|-------|------|---------|-----------|
| Knows | K | Enumerate, describe, list | Written, MCQ, viva |
| Knows How | KH | Explain how to apply | Short notes, case discussion |
| Shows How | SH | Demonstrate in supervised setting | OSCE, OSPE, skills lab |
| Performs | P | Independent performance | Bedside (supervised), internship |

Plus: `is_core` = Y (must achieve for graduation) or N (desirable).

### CRMI Rules

- 7 mandatory rotations totalling 12 months
- 75% attendance per rotation (not aggregate)
- Maximum 15 days leave total across all rotations
- All rotations satisfactorily completed → CRMI Completion Certificate
- CRMI completion is prerequisite for permanent registration with Medical Council

### Compliance Tests Hard-Fail the Build

Every NMC regulation maps to one or more tests in `tests/compliance/`. The pre-commit hook runs the full compliance suite. **One failing test blocks all commits.**

See `tests/NMC_COMPLIANCE_TESTS.md` for the complete test list.

## 12. Offline-First Mobile

### Architecture

Flutter app uses SQLite (via drift) for local storage. The app is fully functional offline for:
- Attendance marking (QR + manual)
- Clinical logbook entries
- AETCOM session attendance and reflection
- Foundation Course attendance
- DOAP session attendance and rating
- Elective logbook entries
- Viewing timetable (last synced version)
- Viewing lesson plan topics

### Sync Strategy

- Per-entry transactional sync (not batch)
- Failed entries retried 3× with exponential backoff
- Field-level merge for entries (student fields vs faculty fields)
- Conflict resolution: last-write-wins on timestamp for simple fields; union-merge for lists
- Sync status visible in UI

### QR Code Offline Flow

1. Faculty generates QR before class (encodes session_id, date, time window, HMAC signature)
2. Students scan offline — stored locally
3. On sync: server validates HMAC and accepts/rejects

## 13. AI Layer

### AI Academic Assistant

LangGraph + Claude Sonnet 4.6 with MCP-style tool definitions:
- `get_student_attendance(student_id, subject_id)`
- `get_batch_at_risk(batch_id)`
- `get_syllabus_coverage(course_id)`
- `get_faculty_teaching_load(faculty_id)`
- `generate_accreditation_report(report_type)`
- `get_exam_eligibility(student_id, exam_id)`
- `get_student_logbook_completion(student_id, phase)`
- `get_aetcom_progress(student_id, phase)`
- `get_elective_eligibility(student_id)`
- `get_competency_attainment(batch_id, subject_code)`

The AI respects the same RBAC as the rest of the platform.

### Multi-language Support

English, Bengali, Hindi from launch.

### AI Copilots

- **Faculty Copilot:** auto-generate lesson plans, question papers, rubrics, attendance insights
- **Student Copilot:** personalised exam prep, topic summaries, attendance advice
- **Management Assistant:** "Show departments at accreditation risk", predictive queries

### Predictive Models

Vertex AI custom models retrained each semester:
- At-risk student detection (risk score 0–100)
- Exam failure prediction (4 weeks before exam)
- Dropout early warning
- Logbook completion risk
- Elective eligibility risk

## 14. Security & DPDP Compliance

### DPDP Act 2023 Compliance

| Requirement | Implementation |
|-------------|---------------|
| Explicit consent | First-login consent screen with timestamped storage |
| Right to access | `/api/v1/me/data-export` endpoint |
| Right to erasure | Soft delete + 7-year retention exception + anonymisation after retention |
| Data minimisation | Field-level audit on every collection point |
| Data residency in India | GCP asia-south1, asia-south2 only |
| Breach notification within 72h | Automated alert pipeline to DPO |
| Audit trail | Append-only `audit_log` table |

### Security Controls

- Encryption at rest: AES-256 (Cloud SQL, Cloud Storage)
- Encryption in transit: TLS 1.3 mandatory
- MFA for admin/principal/dean/CoE roles
- PAM with approval workflow for admin access
- SIEM with anomaly detection
- Quarterly penetration testing
- Weekly vulnerability scans
- DLP policies on Cloud Storage

---

# Layer 3: WHEN & WHY

## 15. Solo Developer + Agent Framework

Synaptix is built by a **single developer (Sila Singh Ghosh) supervising AI agents** through Google Antigravity.

### Agent Specialisation

11 specialist agents (see `agents/` directory):

1. **Orchestrator** — coordinates other agents
2. **Architect** — schema, API contracts, ADRs
3. **Backend** — FastAPI services, business logic
4. **Frontend** — Next.js web app
5. **Mobile** — Flutter app, offline sync
6. **Database** — migrations, indexes, RLS
7. **Testing** — unit, integration, NMC compliance tests
8. **Security** — auth, RBAC, tenant isolation, DPDP
9. **Code Reviewer** — reviews other agents' work
10. **DevOps** — Docker, Cloud Run, Terraform, CI/CD
11. **Documentation** — updates all docs after every session
12. **NMC Compliance** — validates against CBME 2019/2023

Each agent has bounded scope (cannot modify files outside specialisation).

### Build Strategy: Aggressive Scaffold + Iterate

**Weeks 1–4:** All 49 modules scaffolded (every service has its skeleton, every table exists, every test file is stubbed)

**Weeks 5–12:** 15 core modules brought to MVP quality

**Months 4–9:** 31 core modules brought to production quality

**Months 10–18:** Remaining modules + AI layer + polish

### Quality Enforcement

Because a solo developer cannot review every line, quality is enforced by:

1. **Test Coverage Manifest** — `tests/COVERAGE_MANIFEST.yaml` lists every required test case. Build fails if any are missing.
2. **NMC Compliance Hard-Fail** — any failing NMC test blocks all commits.
3. **Tenant Isolation by Middleware** — agents cannot skip tenant filtering; it's enforced at the framework level.
4. **Documentation as Build Artefact** — pre-commit hook rejects commits without doc updates.
5. **Specialist Boundaries** — agents cannot modify files outside their specialisation.

## 16. Testing Strategy

### Test Pyramid

| Level | Count Target | Owner | Run On |
|-------|--------------|-------|--------|
| Unit | 5000+ | Agent-generated, spec-driven | Every commit |
| Integration | 800+ | Agent-generated, spec-driven | Every commit |
| Compliance | 200+ | Human-written spec, agent-implemented | Every commit (HARD FAIL) |
| E2E | 50+ | Manual + automation | Pre-release |
| Load | 10+ | Manual setup | Pre-release |
| Security | 30+ | Agent + manual | Weekly |
| Edge Case | 80+ | Human-written spec, agent-implemented | Every commit |
| Mutation | Critical paths | Manual setup | Weekly |

### Coverage Manifest

`tests/COVERAGE_MANIFEST.yaml` is the source of truth for required tests. Every module has a section listing required test cases by name. The test enforcement agent verifies all are implemented.

### NMC Compliance Tests

`tests/NMC_COMPLIANCE_TESTS.md` lists every NMC regulation as a test case. Examples:
- "Student with exactly 75.00% theory attendance is ELIGIBLE for theory exam"
- "Student with 74.99% theory attendance is BLOCKED"
- "CRMI intern at 15 days leave cannot apply for further leave"
- "NExT eligibility requires elective logbook submitted for both blocks"

### Edge Case Database

`tests/EDGE_CASES.md` lists 80+ edge cases including all 33 from the v4.0 audit plus additional discoveries.

### Mutation Testing

For critical paths (attendance calculation, NExT eligibility, logbook IA), mutmut runs weekly to verify tests actually catch bugs.

## 17. Delivery Phases

**18-month plan with aggressive scaffold strategy:**

### Phase 0: Framework Setup (Current — Week 1–2)
Already in progress. This document, agents, tests, conventions.

### Phase 1A: Foundation (Months 1–2)
- F-01 Identity (with MFA), F-02 MDM, F-03 Workflow
- A-01 Academic Structure, A-03 Timetable
- I-01 Student Lifecycle
- Z-01 Security baseline, Z-02 Monitoring
- Local dev environment fully working
- CI/CD pipeline operational
- Data migration M1 (students, faculty, departments)

### Phase 1B: Calendar & Planning (Months 3–4)
- A-04 Calendar Engine (with all NMC event types)
- A-05 Lesson Plans, A-06 Session Tracking
- A-02 Curriculum Migration Engine
- A-07 Foundation Course & AETCOM (basic tracking)
- Data migration M2 (attendance history, exam results)

### Phase 2: Attendance & Admissions (Months 5–7)
- A-11 Attendance Engine (two-threshold)
- A-08 Electives, A-09 DOAP, A-10 Logbook
- A-12 Leave Management
- I-02 Admission Module
- F-04 Notifications, F-05 WhatsApp Bot
- Z-03 Disaster Recovery
- Offline mobile app (Android)
- Data migration M3

### Phase 3: Exams & Resources (Months 8–9)
- A-13 Exam Management (with DOPS, mini-CEX, OSPE/OSCE)
- A-14 Result Management
- A-15 OBE
- I-04 Faculty Management (with Curriculum Committee, MEU)
- I-10 Resource Management
- F-06 Document Generation (NExT eligibility certificate)

### Phase 4: Clinical & Medical Ed (Months 10–12)
- M-01 Clinical, M-02 CBE, M-03 CRMI
- M-04 Hospital Integration (using existing JMN HIMS)
- I-03 Student Success Centre
- I-09 Outreach (Family Adoption Programme)
- iOS app

### Phase 5: Compliance & Intelligence (Months 13–15)
- I-05 Research, I-06 Accreditation, I-07 Evidence Locker, I-08 IQAC
- F-07 Digital Assets
- X-01 Analytics, X-02 Warehouse, I-12 Command Center
- N-02 Fee Portal integration

### Phase 6: AI & Advanced (Months 16–18)
- X-03 AI Assistant, X-04 Copilots, X-05 Predictive
- I-11 Hostel, I-13 Placement, I-14 Alumni
- N-03 API Marketplace

## 18. Edge Cases Catalogue

All edge cases are tracked in `tests/EDGE_CASES.md`. Summary of critical ones:

### From v4.0 Audit (33 items)

**Critical (must fix before Phase 1A):**
- E1: Lateral entry students from other institutions
- E2: Detained / year-back students

**High priority:**
- E3: Partial pass in supplementary exams
- E4: CRMI extension due to attendance shortfall
- F1: Offline sync large backlog handling
- F4: WhatsApp bot re-verification and revocation
- D2: Logbook entry backdating rules
- O1: Mid-year faculty transfer / resignation
- O2: NMC inspector real-time access workflow
- S1: Right to erasure vs academic record retention

**Medium priority:** 15 additional cases

### Additional Edge Cases Discovered in Feasibility Analysis

- Timezone handling (IST vs UTC)
- Academic year boundary (sessions spanning midnight)
- Student name changes
- Duplicate student enrollment
- Faculty teaching across institutions
- Decimal vs integer marks in different assessment types
- Phase transition (back-to-back, no gap)
- NMC inspection during system downtime
- Student death or medical emergency
- Bulk attendance marking errors
- Power outage during sync
- Multiple devices per student
- Faculty marking wrong batch
- University affiliation changes
- Ragging complaint workflow

## 19. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Solo developer burnout | High | Critical | Aggressive scaffold + iteration; strict scope discipline |
| Agent generates non-NMC-compliant code | Medium | Critical | Hard-fail NMC compliance tests; NMC compliance agent reviews |
| Tenant data leakage | Low | Critical | 3-layer enforcement (gateway, middleware, RLS) |
| Cloud cost overrun | Medium | Medium | Tier-based scaling with explicit triggers |
| WhatsApp API cost spike | Medium | Medium | Use SMS/push for routine; WhatsApp for critical only |
| Hospital HIMS integration complexity | High | High | JMN HIMS already exists — use direct integration |
| Data migration quality | High | High | Validation rules, 30-day parallel run, HOD sign-off |
| Faculty adoption resistance | High | High | WhatsApp bot as entry point; champion-led rollout |
| Antigravity rate limits | High | Medium | Claude fallback; structured per-session work |
| Agent context drift | High | High | Persistent memory system; mandatory session protocols |
| Single-developer dependency | High | Critical | Comprehensive docs; agent-readable codebase; knowledge transfer |

## 20. Open Decisions

Items requiring decisions before or during development:

### Academic & Regulatory
- [ ] **DPO appointment** — required before production launch
- [ ] **Breach notification contacts** — 2–3 people, required before production
- [ ] Family Adoption Programme village confirmation (Birohi Gram Panchayat — placeholder)
- [ ] Curriculum Committee members for JMN
- [ ] MEU faculty for JMN

### Technical
- [ ] GCP project name (to be created)
- [ ] Domain name (`platform.jmn.edu.in`? confirmation deferred)
- [ ] Anthropic API key (deferred per Sila's instruction)
- [ ] Gemini API key for fallback (deferred)
- [ ] WhatsApp Business API provider (Gupshup vs Twilio India)
- [ ] SMS gateway choice (Textlocal vs Gupshup vs MSG91)

### Operational
- [ ] Faculty champions per department (target: before Phase 1A go-live)
- [ ] First UAT cohort identification

---

*Synaptix Master Specification v5.0*
*Last updated: 2026-06-18*
*Owner: Sila Singh Ghosh, Chairperson, Nirmala Foundation*
*Status: Active — superseding all prior versions*
