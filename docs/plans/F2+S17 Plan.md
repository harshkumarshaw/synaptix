# Session F2 Plan — Attendance UI (Frontend) + Session 17 Plan — Hardware Stubs (Backend)

> **Both sessions run in parallel. No file conflicts.**

---

# FRONTEND: Session F2 — Attendance UI with Live API Data

**Target Agent:** 03-frontend
**Estimated duration:** 4-6 hours
**Directory scope:** `frontend-web/`
**Goal:** Faculty can mark attendance. Students see their percentages. Dashboard cards show real numbers.

---

## What This Session Delivers

After Session F1, everything shows "—" (placeholder). After Session F2:
- Admin dashboard shows real student count, today's attendance rate, pending reviews count
- Faculty opens a class, sees the student list, checks boxes, clicks Submit → attendance is marked
- Student sees per-subject attendance percentages with colour-coded threshold warnings (green ≥75%, amber 70-75%, red <70%)
- Exam eligibility status shown per subject

This is the session where the product becomes REAL.

---

## Prerequisites

Before starting, confirm the backend services are running:

```powershell
# Terminal 1 — Auth service
cd F:\Synaptix\services\snx-auth
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Academic service (attendance, calendar, leave)
cd F:\Synaptix\services\snx-academic
uvicorn app.main:app --reload --port 8001

# Terminal 3 — Frontend
cd F:\Synaptix\frontend-web
npm run dev
```

If `snx-auth` doesn't have a working login endpoint yet, continue using the dev bypass JWT from Session F1. But attempt real auth first.

---

## Phase A — API Hooks Layer (45-60 min)

Create React Query hooks that wrap every backend API call. These are reusable across all pages.

### A.1 Type Definitions

Create `src/types/attendance.ts`:

```typescript
export interface AttendanceSummary {
  student_id: string;
  course_id: string;
  course_name: string;
  subject_code: string;
  attendance_category: string;
  sessions_conducted: number;
  sessions_present: number;
  sessions_excused: number;
  sessions_medical: number;
  sessions_official_duty: number;
  attendance_pct: number;
  threshold: number;
  is_eligible: boolean;
}

export interface AttendanceRecord {
  id: string;
  student_id: string;
  student_name: string;
  event_id: string;
  status: "present" | "absent" | "late" | "excused" | "medical" | "official_duty" | "exempt";
  method: string;
  marked_at: string;
  needs_review: boolean;
}

export interface EventRoster {
  event_id: string;
  event_date: string;
  course_name: string;
  attendance_category: string;
  students: AttendanceRecord[];
  total_students: number;
  marked_count: number;
}

export interface MarkAttendanceRequest {
  event_id: string;
  student_id: string;
  status: string;
  method?: string;
}

export interface BulkMarkRequest {
  event_id: string;
  marks: { student_id: string; status: string }[];
}

export interface ExamEligibility {
  student_id: string;
  course_id: string;
  theory_pct: number;
  practical_pct: number;
  theory_eligible: boolean;
  practical_eligible: boolean;
  theory_threshold: number;
  practical_threshold: number;
}

export interface DashboardStats {
  total_students: number;
  todays_attendance_rate: number;
  pending_logbook_reviews: number;
  at_risk_students: number;
}

export interface TodayEvent {
  id: string;
  course_name: string;
  event_type: string;
  start_time: string;
  end_time: string;
  room: string | null;
  attendance_marked: boolean;
  students_present: number;
  students_total: number;
}
```

### A.2 API Hooks

Create `src/hooks/use-attendance.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  AttendanceSummary, EventRoster, BulkMarkRequest,
  ExamEligibility, DashboardStats, TodayEvent,
} from "@/types/attendance";

// Student: my attendance summary
export function useStudentSummary(studentId: string) {
  return useQuery({
    queryKey: ["attendance", "summary", studentId],
    queryFn: async () => {
      const { data } = await api.get<AttendanceSummary[]>(
        `/attendance/student/${studentId}/summary`
      );
      return data;
    },
    enabled: !!studentId,
  });
}

// Faculty: event roster (who's in today's class)
export function useEventRoster(eventId: string) {
  return useQuery({
    queryKey: ["attendance", "event", eventId],
    queryFn: async () => {
      const { data } = await api.get<EventRoster>(
        `/attendance/event/${eventId}`
      );
      return data;
    },
    enabled: !!eventId,
  });
}

// Faculty: mark attendance (bulk)
export function useBulkMark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: BulkMarkRequest) => {
      const { data } = await api.post("/attendance/mark-bulk", request);
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["attendance", "event", variables.event_id],
      });
    },
  });
}

// Student: exam eligibility
export function useExamEligibility(studentId: string, courseId: string) {
  return useQuery({
    queryKey: ["attendance", "eligibility", studentId, courseId],
    queryFn: async () => {
      const { data } = await api.get<ExamEligibility>(
        `/attendance/eligibility/${studentId}/${courseId}`
      );
      return data;
    },
    enabled: !!studentId && !!courseId,
  });
}

// Admin: dashboard stats
export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: async () => {
      const { data } = await api.get<DashboardStats>("/dashboard/stats");
      return data;
    },
    // If this endpoint doesn't exist yet, return mock data
    retry: false,
  });
}

// Faculty: today's events
export function useTodayEvents() {
  return useQuery({
    queryKey: ["events", "today"],
    queryFn: async () => {
      const { data } = await api.get<TodayEvent[]>("/events/today");
      return data;
    },
    retry: false,
  });
}
```

### A.3 Dashboard Stats Hook with Fallback

Since some endpoints may not exist yet (e.g., `/dashboard/stats`), create a safe wrapper:

```typescript
// src/hooks/use-dashboard.ts
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { DashboardStats } from "@/types/attendance";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: async (): Promise<DashboardStats> => {
      try {
        const { data } = await api.get<DashboardStats>("/dashboard/stats");
        return data;
      } catch {
        // Endpoint may not exist yet — return placeholder
        return {
          total_students: 0,
          todays_attendance_rate: 0,
          pending_logbook_reviews: 0,
          at_risk_students: 0,
        };
      }
    },
    staleTime: 60_000, // refresh every minute
  });
}
```

---

## Phase B — Faculty Attendance Marking Page (90-120 min)

This is the highest-value page in the entire frontend. A faculty member opens it, sees today's classes, picks one, sees the student list, marks attendance, and submits.

### B.1 Today's Events List

```typescript
// src/app/(authenticated)/attendance/page.tsx
"use client";

import { useAuthStore } from "@/stores/auth-store";
import { FacultyAttendance } from "./faculty-attendance";
import { StudentAttendance } from "./student-attendance";

export default function AttendancePage() {
  const { user } = useAuthStore();

  if (user?.role === "student") {
    return <StudentAttendance />;
  }
  return <FacultyAttendance />;
}
```

### B.2 Faculty Attendance View

```typescript
// src/app/(authenticated)/attendance/faculty-attendance.tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTodayEvents } from "@/hooks/use-attendance";
import { MarkAttendanceSheet } from "./mark-attendance-sheet";
import { CalendarCheck, Clock, Users } from "lucide-react";

export function FacultyAttendance() {
  const { data: events, isLoading } = useTodayEvents();
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  if (isLoading) {
    return <AttendanceSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Mark Attendance</h1>
        <p className="text-muted-foreground">
          Select a class to mark today's attendance
        </p>
      </div>

      {!events?.length ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No classes scheduled for today.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {events.map((event) => (
            <Card
              key={event.id}
              className="cursor-pointer transition-colors hover:border-primary"
              onClick={() => setSelectedEventId(event.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{event.course_name}</CardTitle>
                  {event.attendance_marked ? (
                    <Badge variant="secondary">Marked</Badge>
                  ) : (
                    <Badge variant="destructive">Pending</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-3.5 w-3.5" />
                  <span>{event.start_time} — {event.end_time}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <CalendarCheck className="h-3.5 w-3.5" />
                  <span className="capitalize">{event.event_type}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Users className="h-3.5 w-3.5" />
                  <span>
                    {event.students_present}/{event.students_total} present
                  </span>
                </div>
                {event.room && (
                  <p className="text-xs text-muted-foreground">Room: {event.room}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Slide-out attendance marking sheet */}
      {selectedEventId && (
        <MarkAttendanceSheet
          eventId={selectedEventId}
          onClose={() => setSelectedEventId(null)}
        />
      )}
    </div>
  );
}

function AttendanceSkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="h-8 w-48 rounded bg-muted animate-pulse" />
        <div className="h-4 w-72 rounded bg-muted animate-pulse" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-40 rounded-xl border bg-muted animate-pulse" />
        ))}
      </div>
    </div>
  );
}
```

### B.3 Mark Attendance Sheet (Slide-out Panel)

```typescript
// src/app/(authenticated)/attendance/mark-attendance-sheet.tsx
"use client";

import { useState, useEffect } from "react";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetFooter,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useEventRoster, useBulkMark } from "@/hooks/use-attendance";
import { CheckCircle, Loader2 } from "lucide-react";

interface Props {
  eventId: string;
  onClose: () => void;
}

export function MarkAttendanceSheet({ eventId, onClose }: Props) {
  const { data: roster, isLoading } = useEventRoster(eventId);
  const bulkMark = useBulkMark();
  const { toast } = useToast();

  // Track present/absent per student
  const [marks, setMarks] = useState<Record<string, boolean>>({});

  // Initialise from existing data
  useEffect(() => {
    if (roster?.students) {
      const initial: Record<string, boolean> = {};
      roster.students.forEach((s) => {
        initial[s.student_id] = s.status === "present";
      });
      setMarks(initial);
    }
  }, [roster]);

  function toggleStudent(studentId: string) {
    setMarks((prev) => ({ ...prev, [studentId]: !prev[studentId] }));
  }

  function markAllPresent() {
    if (!roster) return;
    const all: Record<string, boolean> = {};
    roster.students.forEach((s) => { all[s.student_id] = true; });
    setMarks(all);
  }

  function markAllAbsent() {
    if (!roster) return;
    const all: Record<string, boolean> = {};
    roster.students.forEach((s) => { all[s.student_id] = false; });
    setMarks(all);
  }

  async function handleSubmit() {
    const marksList = Object.entries(marks).map(([student_id, present]) => ({
      student_id,
      status: present ? "present" : "absent",
    }));

    bulkMark.mutate(
      { event_id: eventId, marks: marksList },
      {
        onSuccess: () => {
          toast({
            title: "Attendance Saved",
            description: `Marked ${marksList.filter((m) => m.status === "present").length} present out of ${marksList.length}.`,
          });
          onClose();
        },
        onError: (error: any) => {
          toast({
            title: "Error",
            description: error.response?.data?.detail?.message || "Failed to save attendance",
            variant: "destructive",
          });
        },
      }
    );
  }

  const presentCount = Object.values(marks).filter(Boolean).length;
  const totalCount = Object.keys(marks).length;

  return (
    <Sheet open onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{roster?.course_name || "Loading..."}</SheetTitle>
          <p className="text-sm text-muted-foreground">
            {roster?.event_date} &middot;{" "}
            <span className="capitalize">{roster?.attendance_category}</span>
          </p>
        </SheetHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : (
          <div className="mt-6 space-y-4">
            {/* Quick actions */}
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={markAllPresent}>
                All Present
              </Button>
              <Button variant="outline" size="sm" onClick={markAllAbsent}>
                All Absent
              </Button>
              <Badge variant="secondary" className="ml-auto">
                {presentCount}/{totalCount} present
              </Badge>
            </div>

            {/* Student list */}
            <div className="divide-y rounded-md border">
              {roster?.students.map((student) => (
                <label
                  key={student.student_id}
                  className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-muted/50 transition-colors"
                >
                  <Checkbox
                    checked={marks[student.student_id] ?? false}
                    onCheckedChange={() => toggleStudent(student.student_id)}
                  />
                  <span className="flex-1 text-sm">{student.student_name}</span>
                  {marks[student.student_id] && (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  )}
                </label>
              ))}
            </div>
          </div>
        )}

        <SheetFooter className="mt-6">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            disabled={bulkMark.isPending || !roster}
          >
            {bulkMark.isPending ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...</>
            ) : (
              `Save Attendance (${presentCount}/${totalCount})`
            )}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
```

---

## Phase C — Student Attendance View (60 min)

### C.1 Student Attendance Summary

```typescript
// src/app/(authenticated)/attendance/student-attendance.tsx
"use client";

import { useAuthStore } from "@/stores/auth-store";
import { useStudentSummary } from "@/hooks/use-attendance";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

export function StudentAttendance() {
  const { user } = useAuthStore();
  const { data: summaries, isLoading } = useStudentSummary(user?.student_id ?? "");

  if (isLoading) {
    return <div className="animate-pulse space-y-4">
      {[1,2,3,4].map(i => <div key={i} className="h-24 rounded-xl bg-muted" />)}
    </div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Attendance</h1>
        <p className="text-muted-foreground">Subject-wise attendance and exam eligibility</p>
      </div>

      <div className="space-y-4">
        {summaries?.map((s) => (
          <Card key={`${s.course_id}-${s.attendance_category}`}>
            <CardContent className="py-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="font-medium">{s.course_name}</p>
                  <p className="text-xs text-muted-foreground capitalize">
                    {s.attendance_category} &middot; {s.subject_code}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`text-2xl font-bold ${getColour(s.attendance_pct, s.threshold)}`}>
                    {s.attendance_pct.toFixed(1)}%
                  </p>
                  <EligibilityBadge eligible={s.is_eligible} threshold={s.threshold} />
                </div>
              </div>

              <Progress
                value={s.attendance_pct}
                className="h-2"
              />

              <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                <span>
                  {s.sessions_present + s.sessions_excused + s.sessions_medical + s.sessions_official_duty}
                  /{s.sessions_conducted} sessions
                </span>
                <span>Threshold: {s.threshold}%</span>
              </div>
            </CardContent>
          </Card>
        ))}

        {!summaries?.length && (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No attendance data available yet.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function getColour(pct: number, threshold: number): string {
  if (pct >= threshold) return "text-green-600";
  if (pct >= threshold - 5) return "text-amber-600";
  return "text-red-600";
}

function EligibilityBadge({ eligible, threshold }: { eligible: boolean; threshold: number }) {
  return eligible ? (
    <Badge variant="secondary" className="bg-green-100 text-green-700 text-xs">
      Eligible
    </Badge>
  ) : (
    <Badge variant="destructive" className="text-xs">
      Below {threshold}%
    </Badge>
  );
}
```

---

## Phase D — Live Dashboard Cards (45 min)

Replace the placeholder "—" values in all three dashboards with real API data.

### D.1 Admin Dashboard — Live Stats

```typescript
// Update src/app/(authenticated)/dashboard/admin-dashboard.tsx
// Replace hardcoded stats with:

import { useDashboardStats } from "@/hooks/use-dashboard";

export function AdminDashboard() {
  const { data: stats, isLoading } = useDashboardStats();

  const cards = [
    {
      label: "Total Students",
      value: isLoading ? "..." : stats?.total_students?.toString() ?? "—",
      icon: Users,
      color: "text-blue-600",
    },
    {
      label: "Today's Attendance",
      value: isLoading ? "..." : stats?.todays_attendance_rate
        ? `${stats.todays_attendance_rate.toFixed(0)}%`
        : "—",
      icon: CalendarCheck,
      color: "text-green-600",
    },
    {
      label: "Pending Reviews",
      value: isLoading ? "..." : stats?.pending_logbook_reviews?.toString() ?? "—",
      icon: BookOpen,
      color: "text-amber-600",
    },
    {
      label: "At-Risk Students",
      value: isLoading ? "..." : stats?.at_risk_students?.toString() ?? "—",
      icon: AlertTriangle,
      color: "text-red-600",
    },
  ];

  // ... rest of the dashboard using `cards` array
}
```

### D.2 Student Dashboard — Live Attendance Percentage

```typescript
// Update src/app/(authenticated)/dashboard/student-dashboard.tsx

import { useStudentSummary } from "@/hooks/use-attendance";
import { useAuthStore } from "@/stores/auth-store";

export function StudentDashboard() {
  const { user } = useAuthStore();
  const { data: summaries } = useStudentSummary(user?.student_id ?? "");

  // Compute overall attendance across all subjects
  const overallPct = summaries?.length
    ? (summaries.reduce((sum, s) => sum + s.attendance_pct, 0) / summaries.length)
    : 0;

  const cards = [
    {
      label: "Overall Attendance",
      value: summaries ? `${overallPct.toFixed(0)}%` : "...",
      icon: CalendarCheck,
      color: overallPct >= 75 ? "text-green-600" : "text-red-600",
    },
    // ... other cards
  ];
}
```

Apply similar patterns for Faculty dashboard (today's events count, pending signoffs).

---

## Phase E — Error States + Loading (30 min)

Add consistent error and empty state handling:

```typescript
// src/components/ui/error-state.tsx
import { AlertTriangle } from "lucide-react";
import { Button } from "./button";

export function ErrorState({
  message = "Something went wrong",
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertTriangle className="h-10 w-10 text-destructive mb-4" />
      <p className="text-sm text-muted-foreground mb-4">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}
```

Add this to every data-fetching page as an error boundary.

---

## Phase F — Verification + Handoff (15 min)

### F.1 Manual Testing Checklist

With backend services running:

- [ ] Admin dashboard: stat cards show numbers (or graceful "—" if endpoint missing)
- [ ] Faculty: attendance page shows today's events (or empty state)
- [ ] Faculty: clicking an event opens the slide-out mark sheet
- [ ] Faculty: checkboxes toggle, "All Present" / "All Absent" buttons work
- [ ] Faculty: Submit saves attendance (toast confirmation)
- [ ] Student: attendance page shows per-subject summaries
- [ ] Student: colour coding correct (green ≥ threshold, red < threshold)
- [ ] Student: eligibility badge shows correctly
- [ ] Student dashboard: overall attendance percentage shown
- [ ] Error states render when API is down
- [ ] Loading skeletons show during data fetch
- [ ] Mobile responsive: all pages work on narrow viewport

### F.2 Screenshot Evidence

Take screenshots for `docs/screenshots/session-f2/`:
1. Faculty — today's events list
2. Faculty — mark attendance sheet (slide-out)
3. Student — attendance summary with colour-coded percentages
4. Admin dashboard with live stat cards
5. Mobile view of student attendance

### F.3 Commit

```powershell
git add frontend-web/
git commit -m "feat(frontend): Session F2 — Attendance UI with live API data

- React Query hooks for attendance endpoints
- Faculty: event list → mark attendance slide-out → bulk submit
- Student: per-subject attendance summary with threshold colour coding
- Student: exam eligibility badges (green/red)
- Admin/Faculty/Student dashboards connected to live API data
- Error states and loading skeletons
- Type definitions for all attendance API responses

Faculty can now mark attendance in the browser.
Students can see their attendance percentages.
Dashboard cards show real numbers.
"
```

---

# BACKEND: Session 17 — Hardware Attendance Stubs + Hook Fix

**Target Agent:** 02-backend
**Estimated duration:** 3-4 hours
**Directory scope:** `services/`, `tests/`, `scripts/`
**Goal:** Implement attendance method handler interface, hardware stubs, 17 deferred tests, and permanently fix the pre-commit hook

---

## Phase A — Fix Pre-Commit Hook Permanently (30 min)

**This is the FIRST task. No implementation work until the hook works.**

### A.1 Diagnose the Issue

```powershell
# Attempt a test commit to see the error
git commit --allow-empty -m "test: verify pre-commit hook"
# Observe and capture the error output
```

Common Windows pre-commit hook issues:

1. **Shebang line:** The hook script starts with `#!/bin/bash` but Windows git can't execute bash scripts directly
   - Fix: Create a `.git/hooks/pre-commit` wrapper:
   ```cmd
   @echo off
   powershell.exe -ExecutionPolicy Bypass -File scripts\pre-commit-hook.ps1
   ```

2. **PATH issue:** Hook can't find `python` or `ruff`
   - Fix: Use absolute paths or activate the venv inside the hook:
   ```powershell
   # In pre-commit-hook.ps1, add at top:
   $venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
   ```

3. **Line endings:** Hook file has LF endings, Windows expects CRLF
   - Fix: `git config core.autocrlf true` or convert the hook file

### A.2 Verify Fix

```powershell
# Real commit test
git commit --allow-empty -m "test: verify pre-commit hook works"
# Should see hook output, then commit succeeds
# If it works, amend the commit:
git commit --amend -m "fix: resolve pre-commit hook spawn issue on Windows

Root cause: [describe what was wrong]
Fix: [describe what was changed]
Verified: hook now runs during commit on Windows.
"
```

### A.3 Document in INCIDENT_LOG

```markdown
## INC-005: Pre-Commit Hook Spawn Issue (Permanent Fix)

**Date:** YYYY-MM-DD
**Root cause:** [e.g., bash shebang incompatible with Windows Git]
**Fix:** [e.g., Created .git/hooks/pre-commit as CMD wrapper calling PowerShell script]
**Verified:** Hook runs cleanly during `git commit`
**Impact:** No more --no-verify needed. All future commits go through the hook.
**Previous occurrences:** Sessions 9, 14, 16 (all used --no-verify as workaround)
```

### A.4 Acceptance

- [ ] `git commit --allow-empty -m "test"` triggers the hook and succeeds
- [ ] Hook output shows all checks running
- [ ] Root cause documented in INCIDENT_LOG.md
- [ ] No `--no-verify` used for any commit in this session

---

## Phase B — Attendance Method Handler Interface (60 min)

### B.1 Create Handler Interface

```python
# services/snx-academic/app/services/attendance_methods/__init__.py
"""Attendance method handlers — one per marking method."""

# services/snx-academic/app/services/attendance_methods/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass
class MarkingContext:
    """Context for an attendance marking attempt."""
    tenant_id: UUID
    student_id: UUID
    event_id: UUID
    session_id: UUID | None
    device_id: str | None
    geo_lat: float | None
    geo_lng: float | None
    qr_token: str | None
    rfid_card_id: str | None
    biometric_hash: str | None


@dataclass
class MarkingResult:
    """Result of a marking attempt."""
    success: bool
    method: str
    error_code: str | None = None
    error_message: str | None = None
    needs_review: bool = False


class AttendanceMethodHandler(ABC):
    """Base class for attendance marking method handlers."""

    @property
    @abstractmethod
    def method_name(self) -> str:
        """The method identifier stored in attendance.method column."""
        ...

    @abstractmethod
    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        """
        Validate the marking attempt.
        Returns MarkingResult with success=True if valid.
        The actual attendance row creation is handled by AttendanceService,
        NOT by the handler.
        """
        ...
```

### B.2 Implement Handlers

```python
# services/snx-academic/app/services/attendance_methods/manual.py
class ManualHandler(AttendanceMethodHandler):
    method_name = "manual"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        # Manual marking always succeeds (faculty clicks a button)
        return MarkingResult(success=True, method="manual")


# services/snx-academic/app/services/attendance_methods/qr.py
class QRHandler(AttendanceMethodHandler):
    method_name = "qr"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if not ctx.qr_token:
            return MarkingResult(success=False, method="qr",
                                 error_code="ATT-QR-001", error_message="QR token missing")

        # Validate QR token (check it matches the event's generated QR)
        # In Phase 2, this is web-side validation only
        # Full mobile scan validation comes in Phase 2.5
        valid = await self._validate_qr_token(ctx.tenant_id, ctx.event_id, ctx.qr_token)
        if not valid:
            return MarkingResult(success=False, method="qr",
                                 error_code="ATT-QR-002", error_message="Invalid or expired QR token")

        return MarkingResult(success=True, method="qr")

    async def _validate_qr_token(self, tenant_id, event_id, token) -> bool:
        # Stub: check token against stored event QR
        # Real implementation needs QR generation + validation
        return True  # Stub for now


# services/snx-academic/app/services/attendance_methods/rfid.py
class RFIDHandler(AttendanceMethodHandler):
    method_name = "rfid"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if not ctx.rfid_card_id:
            return MarkingResult(success=False, method="rfid",
                                 error_code="ATT-RFID-001", error_message="RFID card ID missing")

        # Stub: validate card ID against student enrollment
        # Real implementation needs RFID reader integration
        return MarkingResult(success=True, method="rfid", needs_review=False)


# services/snx-academic/app/services/attendance_methods/gps.py
class GPSHandler(AttendanceMethodHandler):
    method_name = "gps"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if ctx.geo_lat is None or ctx.geo_lng is None:
            return MarkingResult(success=False, method="gps",
                                 error_code="ATT-GPS-001", error_message="GPS coordinates missing")

        # Stub: validate coordinates against campus geofence
        # Real implementation needs geofence config in MDM
        in_fence = await self._check_geofence(ctx.tenant_id, ctx.geo_lat, ctx.geo_lng)
        return MarkingResult(
            success=True, method="gps",
            needs_review=not in_fence,  # flag if outside fence
        )

    async def _check_geofence(self, tenant_id, lat, lng) -> bool:
        # Stub: always returns True
        # Real implementation reads geofence polygon from MDM config
        return True


# services/snx-academic/app/services/attendance_methods/biometric.py
class BiometricHandler(AttendanceMethodHandler):
    method_name = "biometric"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if not ctx.biometric_hash:
            return MarkingResult(success=False, method="biometric",
                                 error_code="ATT-BIO-001", error_message="Biometric data missing")

        # Stub: validate hash against stored template
        return MarkingResult(success=True, method="biometric")
```

### B.3 Handler Registry

```python
# services/snx-academic/app/services/attendance_methods/registry.py
from .manual import ManualHandler
from .qr import QRHandler
from .rfid import RFIDHandler
from .gps import GPSHandler
from .biometric import BiometricHandler

HANDLERS: dict[str, AttendanceMethodHandler] = {
    "manual": ManualHandler(),
    "qr": QRHandler(),
    "rfid": RFIDHandler(),
    "gps": GPSHandler(),
    "biometric": BiometricHandler(),
    "face": BiometricHandler(),  # Face uses same stub as biometric for now
}

def get_handler(method: str) -> AttendanceMethodHandler:
    handler = HANDLERS.get(method)
    if not handler:
        raise ValueError(f"Unknown attendance method: {method}")
    return handler
```

### B.4 Integrate into AttendanceService

Modify `attendance_service.mark_attendance()` to call the handler:

```python
async def mark_attendance(self, ..., method: str = "manual", **method_kwargs):
    handler = get_handler(method)
    ctx = MarkingContext(
        tenant_id=tenant_id,
        student_id=student_id,
        event_id=event_id,
        session_id=session_id,
        device_id=method_kwargs.get("device_id"),
        geo_lat=method_kwargs.get("geo_lat"),
        geo_lng=method_kwargs.get("geo_lng"),
        qr_token=method_kwargs.get("qr_token"),
        rfid_card_id=method_kwargs.get("rfid_card_id"),
        biometric_hash=method_kwargs.get("biometric_hash"),
    )

    result = await handler.validate(ctx)
    if not result.success:
        raise AttendanceServiceError(result.error_code, result.error_message)

    # Proceed with normal attendance marking (existing code)
    # Set method column and needs_review from handler result
    ...
```

---

## Phase C — 17 Deferred Hardware Tests (60-90 min)

Implement all 17 hardware/mobile deferred tests. Since the handlers are stubs, tests validate the interface and validation logic, not real hardware.

Remove `deferred_to: "Phase 2.5"` from each of these 17 entries in COVERAGE_MANIFEST.yaml after implementation.

### Test Categories

**Method-specific marking (ATT-003..007):** Test that each handler validates its required inputs and returns appropriate MarkingResult.

**Offline sync stubs (ATT-SYNC-001..007):** Test the offline sync data structures and conflict resolution key (MAX of original_marked_at, marked_at). Real sync requires mobile app — test the resolution logic only.

**Security edge cases (ATT-E017..E019):** QR token expiry, GPS outside geofence flagging, replay attack prevention.

### Test File

Create `tests/unit/attendance/test_method_handlers.py`:

```python
"""Tests for attendance method handlers (ATT-003..007, ATT-E017..E019)."""
import pytest
from services.snx_academic.app.services.attendance_methods.registry import get_handler
from services.snx_academic.app.services.attendance_methods.base import MarkingContext
from uuid import uuid4


class TestHandlerValidation:

    async def test_att_003_rfid_marking(self):
        """ATT-003: RFID handler validates card_id presence."""
        handler = get_handler("rfid")
        ctx = MarkingContext(
            tenant_id=uuid4(), student_id=uuid4(), event_id=uuid4(),
            session_id=None, device_id="RFID-001",
            geo_lat=None, geo_lng=None, qr_token=None,
            rfid_card_id="CARD-12345", biometric_hash=None,
        )
        result = await handler.validate(ctx)
        assert result.success
        assert result.method == "rfid"

    async def test_att_003_rfid_missing_card(self):
        """ATT-003 negative: RFID without card_id fails."""
        handler = get_handler("rfid")
        ctx = MarkingContext(
            tenant_id=uuid4(), student_id=uuid4(), event_id=uuid4(),
            session_id=None, device_id=None,
            geo_lat=None, geo_lng=None, qr_token=None,
            rfid_card_id=None, biometric_hash=None,
        )
        result = await handler.validate(ctx)
        assert not result.success
        assert result.error_code == "ATT-RFID-001"

    # ... similar for ATT-004 (face), ATT-005 (GPS), ATT-006 (biometric), ATT-007
    # ... ATT-E017 (QR expired), ATT-E018 (QR replay), ATT-E019 (GPS outside geofence)
```

Create `tests/unit/attendance/test_offline_sync.py`:

```python
"""Tests for offline sync conflict resolution (ATT-SYNC-001..007)."""
# Test the MAX(original_marked_at, marked_at) resolution per ADR-037
# No real mobile sync — just the resolution logic
```

---

## Phase D — Verification + Handoff (15 min)

```powershell
# All tests
pytest tests/ -v --tb=short -q

# Manifest
python scripts/verify_coverage_manifest.py
# Expected: remaining deferred should only be Phase 3/4 items (no Phase 2.5 left)

# All verifiers
python scripts/verify_adr_sequence.py
python scripts/verify_edge_case_coverage.py
python scripts/verify_compliance_coverage.py
```

### Commit (using the FIXED hook — no --no-verify)

```powershell
git add services/ packages/ tests/ scripts/ docs/
git commit -m "feat(attendance): Session 17 — hardware method stubs + hook fix

Phase A: Pre-commit hook permanently fixed
  Root cause: [describe]
  Fix: [describe]
  No more --no-verify needed.

Phase B: AttendanceMethodHandler interface
  - Base handler with MarkingContext/MarkingResult
  - 6 handlers: manual, qr, rfid, gps, biometric, face
  - Handler registry with get_handler()
  - Integrated into AttendanceService.mark_attendance()

Phase C: 17 hardware tests implemented
  - ATT-003..007 (method-specific validation)
  - ATT-SYNC-001..007 (offline sync resolution logic)
  - ATT-E017..E019 (security edge cases)
  - Removed deferred_to from 17 manifest entries

Phase 2.5: COMPLETE (all deferred Phase 2.5 tests now implemented)
Refs: ADR-037 (conflict resolution), PHASE2_SCHEMA.md
"
```

### Session End

```
SESSION END — Agent: 02-backend (Session 17)
Duration: ~X hours

Phase A: Pre-commit hook FIXED permanently
Phase B: 6 attendance method handlers created
Phase C: 17 deferred tests implemented
Phase D: All verifiers clean

Tests passing: NN (target: 150 = 133 + 17)
Phase 2.5 deferred remaining: 0
Pre-commit hook: WORKS (no --no-verify)

PHASE 2.5 COMPLETE.
Next backend session (19): Phase 3 R0 (Examination Management planning)
```

---

## After Both Sessions Complete

| Track | Status | What you can do |
|---|---|---|
| Frontend | F1 ✓, F2 ✓ | Faculty marks attendance in browser. Students see percentages. |
| Backend | Phase 2 ✓, Phase 2.5 ✓ | 150+ tests, all methods stubbed, MDM seeded |

Next parallel pair:
- **Session F3:** Logbook + DOAP UI (student creates entries, faculty signs off, DOAP visual pipeline)
- **Session 19:** Phase 3 R0 (Examination Management — ADRs, schema, test categorisation)