"use client";

import { useAuthStore } from "@/stores/auth-store";
import { LeaveRequestForm } from "./leave-request-form";
import { LeaveHistory } from "./leave-history";
import { ApprovalQueue } from "./approval-queue";

export default function LeavePage() {
  const user = useAuthStore((state) => state.user);

  if (!user) {
    return <div className="p-8 text-center">Loading user session...</div>;
  }

  if (user.role === "student") {
    return (
      <div className="container mx-auto p-6 space-y-8 animate-in fade-in duration-300">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Leave Management</h1>
          <p className="text-muted-foreground text-sm">
            Submit leave requests, track their approval status, and view your academic leave history.
          </p>
        </div>
        <div className="grid gap-8 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <LeaveRequestForm />
          </div>
          <div className="lg:col-span-3">
            <LeaveHistory />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <ApprovalQueue />
    </div>
  );
}
