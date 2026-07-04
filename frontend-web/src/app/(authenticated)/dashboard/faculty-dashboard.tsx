"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarCheck, BookOpen, Stethoscope, Clock } from "lucide-react";

export function FacultyDashboard() {
  const stats = [
    { label: "Today's Classes", value: "—", icon: CalendarCheck, color: "text-blue-600" },
    { label: "Pending Signoffs", value: "—", icon: BookOpen, color: "text-amber-600" },
    { label: "DOAP Assessments Due", value: "—", icon: Stethoscope, color: "text-purple-600" },
    { label: "Leave Requests", value: "—", icon: Clock, color: "text-orange-600" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Faculty Dashboard</h1>
        <p className="text-muted-foreground">Your teaching overview</p>
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
            <CardTitle className="text-base">Today&apos;s Schedule</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Your classes for today will appear here in Session F2.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Logbook Queue</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Student submissions awaiting your review will appear here in Session F4.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
