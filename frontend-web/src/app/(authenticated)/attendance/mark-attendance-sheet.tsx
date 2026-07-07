"use client";

import { useState, useEffect } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { useEventRoster, useBulkMark } from "@/hooks/use-attendance";
import { CheckCircle, Loader2 } from "lucide-react";

interface Props {
  eventId: string;
  onClose: () => void;
}

export function MarkAttendanceSheet({ eventId, onClose }: Props) {
  const { data: roster, isLoading } = useEventRoster(eventId);
  const bulkMark = useBulkMark();

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
    roster.students.forEach((s) => {
      all[s.student_id] = true;
    });
    setMarks(all);
  }

  function markAllAbsent() {
    if (!roster) return;
    const all: Record<string, boolean> = {};
    roster.students.forEach((s) => {
      all[s.student_id] = false;
    });
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
          // Toast omitted for brevity, or we can use normal window.alert
          onClose();
        },
        onError: (error: any) => {
          console.error("Failed to save attendance:", error);
          alert(
            error.response?.data?.detail?.message ||
              "Failed to save attendance",
          );
        },
      },
    );
  }

  const presentCount = Object.values(marks).filter(Boolean).length;
  const totalCount = Object.keys(marks).length;

  return (
    <Sheet
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
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
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={bulkMark.isPending || !roster}
          >
            {bulkMark.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
              </>
            ) : (
              `Save Attendance (${presentCount}/${totalCount})`
            )}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
