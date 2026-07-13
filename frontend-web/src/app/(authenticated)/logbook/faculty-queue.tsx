"use client";

import { useState } from "react";
import { useStudents, useStudentEntries } from "@/hooks/use-logbook";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SignoffSheet } from "./signoff-sheet";
import { LogbookEntry } from "@/types/logbook";
import { BookOpen, User, Calendar, CheckCircle } from "lucide-react";

export default function FacultyQueue() {
  const { data: students, isLoading: loadingStudents } = useStudents();
  const [selectedStudentId, setSelectedStudentId] = useState<string>("");
  const [selectedEntry, setSelectedEntry] = useState<LogbookEntry | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("submitted");

  const {
    data: entries,
    isLoading: loadingEntries,
    refetch,
  } = useStudentEntries(
    selectedStudentId,
    statusFilter === "all" ? undefined : { status: statusFilter },
  );

  const selectedStudent = students?.find((s) => s.id === selectedStudentId);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Logbook Signoff Queue</CardTitle>
          <CardDescription>
            Select a student to review and sign off their digital logbook
            entries.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div className="w-full sm:w-72">
              <label
                htmlFor="student-select"
                className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2"
              >
                Select Student
              </label>
              <select
                id="student-select"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(e.target.value)}
                disabled={loadingStudents}
              >
                <option value="">-- Choose a Student --</option>
                {students?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.full_name} ({s.roll_number})
                  </option>
                ))}
              </select>
            </div>

            {selectedStudentId && (
              <div className="w-full sm:w-auto">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2">
                  Status Filter
                </label>
                <div className="flex gap-2">
                  {["submitted", "approved", "rejected", "all"].map(
                    (status) => (
                      <Button
                        key={status}
                        size="sm"
                        variant={
                          statusFilter === status ? "default" : "outline"
                        }
                        onClick={() => setStatusFilter(status)}
                        className="capitalize"
                      >
                        {status === "all" ? "All Entries" : status}
                      </Button>
                    ),
                  )}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {selectedStudentId ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <User className="h-5 w-5 text-primary" />
              Entries for {selectedStudent?.full_name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingEntries ? (
              <div className="py-8 text-center text-muted-foreground">
                Loading student entries...
              </div>
            ) : !entries || entries.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                No {statusFilter !== "all" ? statusFilter : ""} entries found
                for this student.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Competency</TableHead>
                    <TableHead>Activity</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Signoff Details</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell className="font-semibold">
                        {entry.competency_code}
                        <span className="block text-xs font-normal text-muted-foreground">
                          {entry.subject_code
                            ? `Subject: ${entry.subject_code}`
                            : "Elective Block"}{" "}
                          ({entry.nmc_level})
                        </span>
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
                        <span className="flex items-center gap-1 text-xs">
                          <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                          {entry.activity_date}
                        </span>
                        {entry.backdated && (
                          <Badge
                            variant="outline"
                            className="mt-1 text-amber-500 border-amber-500 bg-amber-500/5 text-[10px]"
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
                          {entry.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {entry.status === "approved" ? (
                          <div className="text-xs space-y-0.5">
                            <p className="font-semibold text-green-600">
                              Certified ✓
                            </p>
                            <p className="text-muted-foreground">
                              Rating: {entry.rating} | Dec:{" "}
                              {entry.faculty_decision}
                            </p>
                            <p className="text-muted-foreground">
                              Initials: {entry.faculty_initials}
                            </p>
                          </div>
                        ) : entry.status === "rejected" ? (
                          <div className="text-xs space-y-0.5">
                            <p className="font-semibold text-red-500">
                              Needs Revision
                            </p>
                            <p className="text-muted-foreground">
                              Dec: {entry.faculty_decision} | Initials:{" "}
                              {entry.faculty_initials}
                            </p>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            Pending review
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {entry.status === "submitted" ? (
                          <Button
                            size="sm"
                            onClick={() => setSelectedEntry(entry)}
                            className="bg-green-600 hover:bg-green-700 text-white"
                          >
                            Signoff
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setSelectedEntry(entry)}
                          >
                            View
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
      ) : (
        <div className="flex flex-col items-center justify-center p-12 border border-dashed rounded-lg bg-card text-center">
          <BookOpen className="h-10 w-10 text-muted-foreground mb-4" />
          <h3 className="font-semibold text-lg">No Student Selected</h3>
          <p className="text-sm text-muted-foreground max-w-sm mt-1">
            Please select a student from the dropdown above to review their
            digital logbook entries and pending requests.
          </p>
        </div>
      )}

      <SignoffSheet
        entry={selectedEntry}
        isOpen={selectedEntry !== null}
        onClose={() => setSelectedEntry(null)}
        onSuccess={() => {
          setSelectedEntry(null);
          refetch();
        }}
      />
    </div>
  );
}
