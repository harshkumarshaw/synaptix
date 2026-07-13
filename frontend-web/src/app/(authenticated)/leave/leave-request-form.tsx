"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { useCreateLeave } from "@/hooks/use-leave";
import { useToast } from "@/hooks/use-toast";
import { FileUp, CalendarRange, Info } from "lucide-react";

export function LeaveRequestForm() {
  const [leaveType, setLeaveType] = useState<string>("casual");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [reason, setReason] = useState<string>("");
  const [fileAttached, setFileAttached] = useState<boolean>(false);

  const createLeave = useCreateLeave();
  const { toast } = useToast();

  // Calculation of requested days duration
  const getDurationDays = () => {
    if (!startDate || !endDate) return 0;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = end.getTime() - start.getTime();
    if (diffTime < 0) return 0;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    return diffDays;
  };

  const duration = getDurationDays();
  const needsMedicalCert = leaveType === "medical" && duration >= 3;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!startDate || !endDate) {
      toast({
        title: "Validation Error",
        description: "Please specify both start and end dates.",
        variant: "destructive",
      });
      return;
    }

    const start = new Date(startDate);
    const end = new Date(endDate);

    if (end < start) {
      toast({
        title: "Validation Error",
        description: "End date must be on or after start date.",
        variant: "destructive",
      });
      return;
    }

    // Check for past dates warning
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (start < today && reason.length < 20) {
      toast({
        title: "Backdated Request",
        description:
          "For backdated leave requests, please provide a detailed reason (minimum 20 characters).",
        variant: "destructive",
      });
      return;
    }

    if (reason.length < 10) {
      toast({
        title: "Validation Error",
        description:
          "Please provide a detailed reason (minimum 10 characters).",
        variant: "destructive",
      });
      return;
    }

    if (needsMedicalCert && !fileAttached) {
      toast({
        title: "Medical Certificate Required",
        description:
          "Medical leave for 3 or more days requires a medical certificate upload.",
        variant: "destructive",
      });
      return;
    }

    createLeave.mutate(
      {
        leave_type: leaveType,
        start_date: startDate,
        end_date: endDate,
        reason: reason,
      },
      {
        onSuccess: () => {
          toast({
            title: "Leave Requested",
            description: "Your leave request has been submitted successfully.",
          });
          // Reset form
          setStartDate("");
          setEndDate("");
          setReason("");
          setFileAttached(false);
        },
        onError: (err: any) => {
          toast({
            title: "Request Failed",
            description:
              err.response?.data?.detail || "Could not submit leave request.",
            variant: "destructive",
          });
        },
      },
    );
  }

  return (
    <Card className="border-primary/10 shadow-lg bg-background/80 backdrop-blur-md">
      <CardHeader>
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <CalendarRange className="h-5 w-5 text-primary" />
          Request Leave
        </CardTitle>
        <CardDescription>
          Submit a new leave application for approval
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Leave Type */}
          <div className="space-y-1.5">
            <label className="text-sm font-semibold">Leave Type</label>
            <select
              value={leaveType}
              onChange={(e) => setLeaveType(e.target.value)}
              className="w-full h-10 px-3 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="casual">Casual Leave</option>
              <option value="medical">Medical Leave</option>
              <option value="academic">Academic Leave</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Dates Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-semibold">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded-lg"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-semibold">End Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full rounded-lg"
              />
            </div>
          </div>

          {/* Duration Indicator */}
          {duration > 0 && (
            <div className="flex items-center gap-2 p-3 bg-muted/40 rounded-lg text-xs font-semibold">
              <Info className="h-4 w-4 text-primary" />
              Duration: {duration} {duration === 1 ? "day" : "days"} requested
            </div>
          )}

          {/* Reason */}
          <div className="space-y-1.5">
            <label className="text-sm font-semibold">
              Reason / Description
            </label>
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="State the reason for leave clearly (min 10 characters)..."
              rows={4}
              className="w-full rounded-lg resize-none"
            />
          </div>

          {/* Medical Certificate Upload */}
          {needsMedicalCert && (
            <div className="space-y-2 p-4 border-2 border-dashed rounded-xl bg-muted/20 flex flex-col items-center justify-center text-center">
              <FileUp className="h-8 w-8 text-primary/60 mb-2" />
              <div className="text-xs font-semibold">
                Upload Medical Certificate
              </div>
              <p className="text-[10px] text-muted-foreground max-w-xs mt-0.5">
                Medical leave for 3 or more days requires verified certification
                (PDF or JPEG, max 5MB).
              </p>
              {fileAttached ? (
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-emerald-500 font-bold">
                    ✓ Certificate attached
                  </span>
                  <button
                    type="button"
                    onClick={() => setFileAttached(false)}
                    className="text-[10px] text-destructive hover:underline"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setFileAttached(true)}
                  className="mt-2 text-xs"
                >
                  Select File
                </Button>
              )}
            </div>
          )}

          <Button
            type="submit"
            className="w-full mt-2 py-6 rounded-lg font-semibold transition-transform hover:-translate-y-0.5"
            disabled={createLeave.isPending}
          >
            {createLeave.isPending
              ? "Submitting Application..."
              : "Submit Application"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
