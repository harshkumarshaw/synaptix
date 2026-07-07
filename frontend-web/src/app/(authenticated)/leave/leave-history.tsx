"use client";

import { useLeaveRequests, useCancelLeave } from "@/hooks/use-leave";
import { useAuthStore } from "@/stores/auth-store";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Calendar, Trash2 } from "lucide-react";

export function LeaveHistory() {
  const user = useAuthStore((state) => state.user);
  const studentId = user?.student_id || user?.id || "";

  const { data: requests, isLoading } = useLeaveRequests({ student_id: studentId });
  const cancelLeave = useCancelLeave();
  const { toast } = useToast();

  const getDurationDays = (startStr: string, endStr: string) => {
    const start = new Date(startStr);
    const end = new Date(endStr);
    const diffTime = end.getTime() - start.getTime();
    if (diffTime < 0) return 0;
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return <Badge className="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border-emerald-500/20">Approved</Badge>;
      case "rejected":
        return <Badge className="bg-red-500/10 hover:bg-red-500/20 text-red-500 border-red-500/20">Rejected</Badge>;
      case "pending":
        return <Badge className="bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500 border-yellow-500/20">Pending</Badge>;
      case "cancelled":
        return <Badge className="bg-muted hover:bg-muted text-muted-foreground border-muted">Cancelled</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  function handleCancel(id: string) {
    cancelLeave.mutate(id, {
      onSuccess: () => {
        toast({
          title: "Leave Cancelled",
          description: "The leave request has been cancelled successfully.",
        });
      },
      onError: (err: any) => {
        toast({
          title: "Cancellation Failed",
          description: err.response?.data?.detail || "Could not cancel leave request.",
          variant: "destructive",
        });
      },
    });
  }

  return (
    <Card className="border-primary/10 shadow-lg bg-background/80 backdrop-blur-md">
      <CardHeader>
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" />
          Leave History
        </CardTitle>
        <CardDescription>Track all your submitted leave requests and their outcomes</CardDescription>
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
            No leave requests submitted yet.
          </div>
        ) : (
          <div className="border rounded-xl overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="font-semibold">Type</TableHead>
                  <TableHead className="font-semibold">Dates</TableHead>
                  <TableHead className="font-semibold text-center">Days</TableHead>
                  <TableHead className="font-semibold">Status</TableHead>
                  <TableHead className="font-semibold text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((req) => {
                  const duration = getDurationDays(req.start_date, req.end_date);
                  const canCancel = req.status === "pending" || req.status === "approved";
                  return (
                    <TableRow key={req.id} className="hover:bg-muted/30 transition-colors">
                      <TableCell className="capitalize font-medium">{req.leave_type}</TableCell>
                      <TableCell className="text-xs">
                        {req.start_date} to {req.end_date}
                      </TableCell>
                      <TableCell className="text-center text-xs font-semibold">{duration}</TableCell>
                      <TableCell>{getStatusBadge(req.status)}</TableCell>
                      <TableCell className="text-right">
                        {canCancel && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleCancel(req.id)}
                            disabled={cancelLeave.isPending}
                            className="h-8 w-8 text-destructive/70 hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
