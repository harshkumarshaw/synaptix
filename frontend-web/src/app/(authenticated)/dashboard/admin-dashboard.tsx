"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarCheck, Users, BookOpen, AlertTriangle } from "lucide-react";
import { useDashboardStats } from "@/hooks/use-dashboard";

export function AdminDashboard() {
  const { data: stats, isLoading } = useDashboardStats();

  const cards = [
    {
      label: "Total Students",
      value: isLoading ? "..." : (stats?.total_students?.toString() ?? "—"),
      icon: Users,
      color: "text-blue-600",
    },
    {
      label: "Today's Attendance",
      value: isLoading
        ? "..."
        : stats?.todays_attendance_rate
          ? `${stats.todays_attendance_rate.toFixed(0)}%`
          : "—",
      icon: CalendarCheck,
      color: "text-green-600",
    },
    {
      label: "Pending Reviews",
      value: isLoading
        ? "..."
        : (stats?.pending_logbook_reviews?.toString() ?? "—"),
      icon: BookOpen,
      color: "text-amber-600",
    },
    {
      label: "At-Risk Students",
      value: isLoading ? "..." : (stats?.at_risk_students?.toString() ?? "—"),
      icon: AlertTriangle,
      color: "text-red-600",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Institution overview</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((stat) => (
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
            <CardTitle className="text-base">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Activity feed will appear here in Session F2.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Upcoming Events</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Calendar events will appear here in Session F2.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
