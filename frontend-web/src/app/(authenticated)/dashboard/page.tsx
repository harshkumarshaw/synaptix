"use client";

import { useAuthStore } from "@/stores/auth-store";
import { AdminDashboard } from "./admin-dashboard";
import { FacultyDashboard } from "./faculty-dashboard";
import { StudentDashboard } from "./student-dashboard";

export default function DashboardPage() {
  const { user } = useAuthStore();

  switch (user?.role) {
    case "admin":
    case "super_admin":
      return <AdminDashboard />;
    case "faculty":
    case "hod":
      return <FacultyDashboard />;
    case "student":
      return <StudentDashboard />;
    default:
      return <StudentDashboard />;
  }
}
