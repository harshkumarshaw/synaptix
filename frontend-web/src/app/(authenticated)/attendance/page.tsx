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
