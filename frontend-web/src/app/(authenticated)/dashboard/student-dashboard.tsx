"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarCheck, BookOpen, Stethoscope, GraduationCap } from "lucide-react";

export function StudentDashboard() {
  const stats = [
    { label: "Overall Attendance", value: "—%", icon: CalendarCheck, color: "text-green-600" },
    { label: "Logbook Entries", value: "—", icon: BookOpen, color: "text-blue-600" },
    { label: "DOAP Progress", value: "—", icon: Stethoscope, color: "text-purple-600" },
    { label: "Elective Status", value: "—", icon: GraduationCap, color: "text-amber-600" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Dashboard</h1>
        <p className="text-muted-foreground">Your academic overview</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Attendance by Subject</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Your subject-wise attendance will appear here in Session F2.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Logbook Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Your recent logbook entries and signoff status will appear here in Session F4.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
