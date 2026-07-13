"use client";

import { useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import {
  useStudentEntries,
  useSubmitEntry,
  useIAAssessment,
} from "@/hooks/use-logbook";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { CreateEntryForm } from "./create-entry-form";
import FacultyQueue from "./faculty-queue";
import { LogbookEntry } from "@/types/logbook";
import {
  BookOpen,
  PlusCircle,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
} from "lucide-react";
import { toast } from "sonner";

export default function LogbookPage() {
  const { user } = useAuthStore();
  const isStudent = user?.role === "student";

  // State for student view
  const studentId = user?.student_id || user?.id || "";
  const [selectedSubject, setSelectedSubject] = useState<string>("ANAT");
  const [selectedPhase, setSelectedPhase] = useState<string>("Phase I");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [submittingEntry, setSubmittingEntry] = useState<LogbookEntry | null>(
    null,
  );
  const [studentInitials, setStudentInitials] = useState("");

  const {
    data: entries,
    isLoading: loadingEntries,
    refetch,
  } = useStudentEntries(
    studentId,
    isStudent
      ? { subject_code: selectedSubject, professional_phase: selectedPhase }
      : undefined,
  );

  const { data: iaAssessment, isLoading: loadingIA } = useIAAssessment(
    studentId,
    selectedSubject,
    selectedPhase,
  );

  const submitMutation = useSubmitEntry();

  const handleSubmitting = async () => {
    if (!submittingEntry) return;
    if (!studentInitials.trim()) {
      toast.error("Initials are required to submit the logbook entry");
      return;
    }
    try {
      await submitMutation.mutateAsync({
        entryId: submittingEntry.id,
        payload: { student_initials: studentInitials },
      });
      toast.success("Entry submitted for faculty review");
      setSubmittingEntry(null);
      setStudentInitials("");
      refetch();
    } catch (err: any) {
      toast.error("Failed to submit entry");
    }
  };

  // If role is faculty/HOD/admin, render the review queue
  if (!isStudent && user) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Logbook Queue</h1>
            <p className="text-sm text-muted-foreground">
              Review and sign off on student digital logbooks
            </p>
          </div>
        </div>
        <FacultyQueue />
      </div>
    );
  }

  // Calculate progress percent
  const total = iaAssessment?.total_entries || 10;
  const completed = iaAssessment?.completed_entries || 0;
  const progressPercent = Math.round((completed / total) * 100);

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">My Digital Logbook</h1>
          <p className="text-sm text-muted-foreground">
            Log and submit your academic session reflections
          </p>
        </div>
        <Button
          onClick={() => setShowCreateDialog(true)}
          className="flex items-center gap-2"
        >
          <PlusCircle className="h-4 w-4" />
          New Log Entry
        </Button>
      </div>

      {/* Selectors and IA Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Controls Card */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Filters</CardTitle>
            <CardDescription>
              Filter logbook entries by subject and phase
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="subject-select">Subject</Label>
              <select
                id="subject-select"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
              >
                <option value="ANAT">Anatomy (ANAT)</option>
                <option value="PHYL">Physiology (PHYL)</option>
                <option value="BIOC">Biochemistry (BIOC)</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phase-select">Professional Phase</Label>
              <select
                id="phase-select"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={selectedPhase}
                onChange={(e) => setSelectedPhase(e.target.value)}
              >
                <option value="Phase I">Phase I</option>
                <option value="Phase II">Phase II</option>
                <option value="Phase III Part I">Phase III Part I</option>
                <option value="Phase III Part II">Phase III Part II</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* IA Summary Card */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Internal Assessment Summary</CardTitle>
            <CardDescription>
              Completion status and IA marks breakdown for {selectedSubject}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingIA ? (
              <div className="h-24 flex items-center justify-center text-muted-foreground">
                Loading IA metrics...
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Completed Entries
                    </p>
                    <p className="text-2xl font-bold">
                      {completed} / {total}
                    </p>
                  </div>
                  <div className="text-right space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      IA Marks Awarded
                    </p>
                    <p className="text-2xl font-bold text-green-600">
                      {iaAssessment?.ia_marks_awarded?.toFixed(2) || "0.00"} /{" "}
                      {iaAssessment?.ia_marks_pct?.toFixed(2) || "4.00"}
                    </p>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="h-3 w-full bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(progressPercent, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{progressPercent}% Complete</span>
                    {iaAssessment?.is_complete ? (
                      <span className="text-green-600 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3" /> Fully Complete
                      </span>
                    ) : (
                      <span className="text-amber-500 font-semibold flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" /> Minimum Required Not
                        Met
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Entries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Logbook Entries</CardTitle>
          <CardDescription>
            A list of your registered activities and their signoff statuses
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingEntries ? (
            <div className="py-8 text-center text-muted-foreground">
              Loading entries...
            </div>
          ) : !entries || entries.length === 0 ? (
            <div className="py-12 text-center border border-dashed rounded-lg">
              <FileSpreadsheet className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <h3 className="font-semibold text-lg">No entries logged</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-xs mx-auto">
                You haven't logged any entries for {selectedSubject} in{" "}
                {selectedPhase} yet. Click "New Log Entry" above to add one.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Competency</TableHead>
                  <TableHead>Activity</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Feedback / Signoff</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="font-semibold">
                      {entry.competency_code} ({entry.nmc_level})
                      {entry.is_core && (
                        <Badge
                          variant="default"
                          className="ml-2 text-[10px] bg-red-500 text-white border-transparent"
                        >
                          Core
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="font-medium block">
                        {entry.activity_name}
                      </span>
                      {entry.reflection && (
                        <span className="text-xs text-muted-foreground italic truncate block max-w-xs">
                          "{entry.reflection}"
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {entry.activity_date}
                      {entry.backdated && (
                        <Badge
                          variant="outline"
                          className="ml-2 text-amber-500 border-amber-500 text-[10px]"
                        >
                          Backdated
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          entry.status === "approved"
                            ? "default"
                            : entry.status === "submitted"
                              ? "secondary"
                              : entry.status === "rejected"
                                ? "destructive"
                                : "outline"
                        }
                        className="capitalize"
                      >
                        {entry.status === "pending"
                          ? "Draft"
                          : entry.status === "rejected"
                            ? "Needs Revision"
                            : entry.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {entry.status === "approved" ? (
                        <div className="text-xs text-muted-foreground">
                          <span className="text-green-600 font-semibold block">
                            Certified ✓
                          </span>
                          Initials: {entry.faculty_initials} | Rating:{" "}
                          {entry.rating}
                        </div>
                      ) : entry.status === "rejected" ? (
                        <div className="text-xs text-muted-foreground">
                          <span className="text-red-500 font-semibold block">
                            Revision Requested
                          </span>
                          Initials: {entry.faculty_initials}
                        </div>
                      ) : entry.status === "submitted" ? (
                        <span className="text-xs text-muted-foreground">
                          Signed: {entry.student_initials} (Submitted)
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          Unsubmitted draft
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {entry.status === "pending" ||
                      entry.status === "rejected" ? (
                        <Button
                          size="sm"
                          onClick={() => setSubmittingEntry(entry)}
                        >
                          Submit
                        </Button>
                      ) : (
                        <Button size="sm" variant="ghost" disabled>
                          Submitted
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Dialog for Create Entry */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>New Logbook Entry</DialogTitle>
          </DialogHeader>
          <div className="py-2">
            <CreateEntryForm
              studentId={studentId}
              onSuccess={() => {
                setShowCreateDialog(false);
                refetch();
              }}
              onCancel={() => setShowCreateDialog(false)}
            />
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog for Submit Confirmation */}
      <Dialog
        open={submittingEntry !== null}
        onOpenChange={(open) => !open && setSubmittingEntry(null)}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Submit Logbook Entry</DialogTitle>
            <DialogDescription>
              To submit this entry for review, please enter your initials as a
              digital signature.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="student_initials">Student Initials</Label>
              <Input
                id="student_initials"
                placeholder="e.g. JD"
                value={studentInitials}
                onChange={(e) => setStudentInitials(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSubmittingEntry(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitting}
              disabled={submitMutation.isPending}
            >
              {submitMutation.isPending ? "Submitting..." : "Confirm & Submit"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
