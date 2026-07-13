"use client";

import { useState } from "react";
import {
  useLeaveRequests,
  useApproveLeave,
  useRejectLeave,
  useLeaveImpactPreview,
} from "@/hooks/use-leave";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
import { Progress } from "@/components/ui/progress";
import {
  Check,
  X,
  ShieldAlert,
  FileText,
  User,
  CalendarDays,
  AlertTriangle,
} from "lucide-react";
import type { LeaveRequest } from "@/types/leave";

export function ApprovalQueue() {
  const { data: requests, isLoading } = useLeaveRequests({
    leave_status: "pending",
  });
  const approveLeave = useApproveLeave();
  const rejectLeave = useRejectLeave();
  const { toast } = useToast();

  const [selectedRequest, setSelectedRequest] = useState<LeaveRequest | null>(
    null,
  );
  const [remarks, setRemarks] = useState<string>("");

  const { data: impactPreview, isLoading: isImpactLoading } =
    useLeaveImpactPreview(selectedRequest?.id || "");

  const getDurationDays = (startStr: string, endStr: string) => {
    const start = new Date(startStr);
    const end = new Date(endStr);
    const diffTime = end.getTime() - start.getTime();
    if (diffTime < 0) return 0;
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
  };

  function handleApprove(id: string) {
    approveLeave.mutate(
      { id, remarks },
      {
        onSuccess: () => {
          toast({
            title: "Leave Approved",
            description: "The leave request has been approved successfully.",
          });
          setSelectedRequest(null);
          setRemarks("");
        },
        onError: (err: any) => {
          toast({
            title: "Approval Failed",
            description:
              err.response?.data?.detail || "Could not approve leave request.",
            variant: "destructive",
          });
        },
      },
    );
  }

  function handleReject(id: string) {
    if (!remarks) {
      toast({
        title: "Remarks Required",
        description: "Please enter a remark explaining the rejection.",
        variant: "destructive",
      });
      return;
    }

    rejectLeave.mutate(
      { id, remarks },
      {
        onSuccess: () => {
          toast({
            title: "Leave Rejected",
            description: "The leave request has been rejected.",
          });
          setSelectedRequest(null);
          setRemarks("");
        },
        onError: (err: any) => {
          toast({
            title: "Rejection Failed",
            description:
              err.response?.data?.detail || "Could not reject leave request.",
            variant: "destructive",
          });
        },
      },
    );
  }

  return (
    <Card className="border-primary/10 shadow-lg bg-background/80 backdrop-blur-md">
      <CardHeader>
        <CardTitle className="text-xl font-extrabold flex items-center gap-2">
          <ShieldAlert className="h-6 w-6 text-primary animate-pulse" />
          Leave Approval Queue
        </CardTitle>
        <CardDescription>
          Review and action student and CRMI intern leave applications
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            <div className="h-10 bg-muted animate-pulse rounded-lg" />
            <div className="h-10 bg-muted animate-pulse rounded-lg" />
            <div className="h-10 bg-muted animate-pulse rounded-lg" />
          </div>
        ) : !requests || requests.length === 0 ? (
          <div className="text-center py-12 text-sm text-muted-foreground font-medium">
            No pending leave requests in the queue.
          </div>
        ) : (
          <div className="border rounded-xl overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Student</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Dates</TableHead>
                  <TableHead className="text-center">Days</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((req) => {
                  const duration = getDurationDays(
                    req.start_date,
                    req.end_date,
                  );
                  return (
                    <TableRow
                      key={req.id}
                      onClick={() => {
                        setSelectedRequest(req);
                        setRemarks("");
                      }}
                      className="cursor-pointer hover:bg-muted/40 transition-colors"
                    >
                      <TableCell className="font-semibold">
                        {req.student_name || "Unknown Student"}
                      </TableCell>
                      <TableCell className="capitalize text-xs font-semibold">
                        {req.leave_type}
                      </TableCell>
                      <TableCell className="text-xs">
                        {req.start_date} to {req.end_date}
                      </TableCell>
                      <TableCell className="text-center text-xs font-bold">
                        {duration}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          className="rounded-lg text-xs font-medium"
                        >
                          Review
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>

      {/* Slide-out detail sheet */}
      <Sheet
        open={!!selectedRequest}
        onOpenChange={(open) => !open && setSelectedRequest(null)}
      >
        <SheetContent className="sm:max-w-md overflow-y-auto">
          {selectedRequest && (
            <div className="space-y-6">
              <SheetHeader>
                <SheetTitle className="text-xl font-bold flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  Leave Details
                </SheetTitle>
                <SheetDescription>
                  Review the leave application below before actioning
                </SheetDescription>
              </SheetHeader>

              {/* Student Detail Card */}
              <div className="p-4 border rounded-xl bg-card space-y-3">
                <div className="flex items-center gap-3">
                  <User className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <div className="text-sm font-semibold">
                      {selectedRequest.student_name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      ID: {selectedRequest.student_id.slice(0, 8)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 border-t pt-3">
                  <CalendarDays className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <div className="text-xs font-semibold capitalize">
                      {selectedRequest.leave_type} Leave ·{" "}
                      {getDurationDays(
                        selectedRequest.start_date,
                        selectedRequest.end_date,
                      )}{" "}
                      days
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      {selectedRequest.start_date} to {selectedRequest.end_date}
                    </div>
                  </div>
                </div>
              </div>

              {/* Application Reason */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">
                  Reason for Application
                </label>
                <div className="p-3 border rounded-xl bg-muted/30 text-sm whitespace-pre-line leading-relaxed">
                  {selectedRequest.reason}
                </div>
              </div>

              {/* Attendance Impact Preview */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground">
                  Attendance Impact Preview
                </label>
                {isImpactLoading ? (
                  <div className="h-10 bg-muted animate-pulse rounded-lg" />
                ) : impactPreview ? (
                  <div className="p-4 border rounded-xl bg-red-500/5 border-red-500/10 text-red-600 dark:text-red-400 space-y-2 text-xs">
                    <p className="font-semibold flex items-center gap-1.5">
                      <AlertTriangle className="h-4 w-4" />
                      Attendance warning threshold violation!
                    </p>
                    <p className="leading-relaxed">
                      If approved, the student's Anatomy attendance will drop
                      from {impactPreview.current_attendance}% to{" "}
                      <span className="font-bold">
                        {impactPreview.predicted_attendance}%
                      </span>
                      , which is below the NMC 75% minimum threshold.
                    </p>
                  </div>
                ) : (
                  <div className="p-3 border rounded-xl bg-muted/20 text-xs text-muted-foreground italic">
                    Impact preview unavailable (No attendance conflict detected)
                  </div>
                )}
              </div>

              {/* Remarks/Feedback */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">
                  Remarks / Action Feedback
                </label>
                <Input
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="Enter approval remarks or reason for rejection..."
                  className="rounded-lg"
                />
              </div>

              {/* Action Buttons */}
              <SheetFooter className="flex-row gap-3 pt-4 border-t">
                <Button
                  variant="outline"
                  className="flex-1 gap-2 border-red-500/20 text-red-500 hover:bg-red-500/10 hover:text-red-600"
                  onClick={() => handleReject(selectedRequest.id)}
                  disabled={rejectLeave.isPending || approveLeave.isPending}
                >
                  <X className="h-4 w-4" />
                  Reject
                </Button>
                <Button
                  className="flex-1 gap-2 bg-emerald-600 hover:bg-emerald-700 text-white"
                  onClick={() => handleApprove(selectedRequest.id)}
                  disabled={rejectLeave.isPending || approveLeave.isPending}
                >
                  <Check className="h-4 w-4" />
                  Approve
                </Button>
              </SheetFooter>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </Card>
  );
}
