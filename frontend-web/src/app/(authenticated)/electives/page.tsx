"use client";

import { useAuthStore } from "@/stores/auth-store";
import { StudentPreferences } from "./student-preferences";
import { AdminAllocation } from "./admin-allocation";

export default function ElectivesPage() {
  const user = useAuthStore((state) => state.user);

  if (!user) {
    return <div className="p-8 text-center">Loading user session...</div>;
  }

  if (user.role === "student") {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <StudentPreferences />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <AdminAllocation />
    </div>
  );
}
