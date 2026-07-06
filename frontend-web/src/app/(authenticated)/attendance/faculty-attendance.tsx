"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
          Select a class to mark today&apos;s attendance
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
                  <CardTitle className="text-base">
                    {event.course_name}
                  </CardTitle>
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
                  <span>
                    {event.start_time} — {event.end_time}
                  </span>
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
                  <p className="text-xs text-muted-foreground">
                    Room: {event.room}
                  </p>
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
          <div
            key={i}
            className="h-40 rounded-xl border bg-muted animate-pulse"
          />
        ))}
      </div>
    </div>
  );
}
