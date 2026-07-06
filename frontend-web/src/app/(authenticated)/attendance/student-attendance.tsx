"use client";

import { useAuthStore } from "@/stores/auth-store";
import { useStudentSummary } from "@/hooks/use-attendance";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

export function StudentAttendance() {
  const { user } = useAuthStore();
  const { data: summaries, isLoading } = useStudentSummary(
    user?.student_id ?? "",
  );

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 rounded-xl bg-muted" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Attendance</h1>
        <p className="text-muted-foreground">
          Subject-wise attendance and exam eligibility
        </p>
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
                  <p
                    className={`text-2xl font-bold ${getColour(s.attendance_pct, s.threshold)}`}
                  >
                    {s.attendance_pct.toFixed(1)}%
                  </p>
                  <EligibilityBadge
                    eligible={s.is_eligible}
                    threshold={s.threshold}
                  />
                </div>
              </div>

              <Progress value={s.attendance_pct} className="h-2" />

              <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                <span>
                  {s.sessions_present +
                    s.sessions_excused +
                    s.sessions_medical +
                    s.sessions_official_duty}
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

function EligibilityBadge({
  eligible,
  threshold,
}: {
  eligible: boolean;
  threshold: number;
}) {
  return eligible ? (
    <Badge
      variant="secondary"
      className="bg-green-100 text-green-700 text-xs hover:bg-green-100"
    >
      Eligible
    </Badge>
  ) : (
    <Badge variant="destructive" className="text-xs">
      Below {threshold}%
    </Badge>
  );
}
