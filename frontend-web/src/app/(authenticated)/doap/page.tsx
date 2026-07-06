"use client";

import { useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useStudents } from "@/hooks/use-logbook";
import { useDoapRecords, useDoapState } from "@/hooks/use-doap";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { DoapPipeline } from "./doap-pipeline";
import { Calendar, User, Stethoscope, FileText, ArrowLeftRight } from "lucide-react";

const PRESET_COMPETENCIES = [
  { code: "AN-1.1", name: "Dissection of upper limb" },
  { code: "AN-2.1", name: "Histology of epithelial tissue" },
  { code: "PY-1.1", name: "Perform hematology experiments" },
  { code: "BI-1.1", name: "Estimation of blood glucose" },
];

export default function DoapPage() {
  const { user } = useAuthStore();
  const isStudent = user?.role === "student";

  const { data: students, isLoading: loadingStudents } = useStudents();
  const [selectedStudentId, setSelectedStudentId] = useState<string>("");
  const [selectedCompetency, setSelectedCompetency] = useState<string>("AN-1.1");
  const [activeStage, setActiveStage] = useState<string | null>("D");

  const studentId = isStudent ? (user?.student_id || user?.id || "") : selectedStudentId;

  const { data: doapState, isLoading: loadingState } = useDoapState(studentId, selectedCompetency);
  const { data: records, isLoading: loadingRecords } = useDoapRecords(studentId, selectedCompetency);

  const selectedStudentObj = students?.find((s) => s.id === studentId);
  const selectedCompetencyObj = PRESET_COMPETENCIES.find((c) => c.code === selectedCompetency);

  // Filter records by clicked active stage
  const stageRecords = records?.filter((r) => r.stage === activeStage) || [];

  const handleStageClick = (stage: string) => {
    setActiveStage(stage);
  };

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div>
        <h1 className="text-2xl font-bold">DOAP Skills Tracker</h1>
        <p className="text-sm text-muted-foreground">
          Track clinical and practical skills progression (Demonstrate → Observe → Assist → Perform)
        </p>
      </div>

      {/* Selectors Card */}
      <Card>
        <CardHeader>
          <CardTitle>DOAP Selection</CardTitle>
          <CardDescription>Select competency and student context to view progress pipeline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {!isStudent && (
              <div className="space-y-2">
                <Label htmlFor="student-select">Select Student</Label>
                <select
                  id="student-select"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={selectedStudentId}
                  onChange={(e) => {
                    setSelectedStudentId(e.target.value);
                    setActiveStage("D");
                  }}
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
            )}

            <div className="space-y-2">
              <Label htmlFor="competency-select">Competency Code</Label>
              <select
                id="competency-select"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={selectedCompetency}
                onChange={(e) => {
                  setSelectedCompetency(e.target.value);
                  setActiveStage("D");
                }}
              >
                {PRESET_COMPETENCIES.map((comp) => (
                  <option key={comp.code} value={comp.code}>
                    {comp.code} - {comp.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {studentId ? (
        <div className="space-y-6">
          {/* Visual Pipeline Section */}
          <Card>
            <CardHeader className="border-b pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Stethoscope className="h-5 w-5 text-primary" />
                Pipeline for {selectedCompetencyObj?.code}: {selectedCompetencyObj?.name}
              </CardTitle>
              {!isStudent && selectedStudentObj && (
                <CardDescription>Viewing DOAP progress for {selectedStudentObj.full_name}</CardDescription>
              )}
            </CardHeader>
            <CardContent className="pt-6">
              {loadingState ? (
                <div className="h-32 flex items-center justify-center text-muted-foreground">
                  Loading DOAP state...
                </div>
              ) : doapState ? (
                <DoapPipeline
                  state={doapState}
                  activeStage={activeStage}
                  onStageClick={handleStageClick}
                />
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  No DOAP history initialized for this student and competency.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Stage Details Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Stage {activeStage} Attempt History
              </CardTitle>
              <CardDescription>
                Click stage nodes above to see detailed feedback, ratings, and certifications.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingRecords ? (
                <div className="text-center py-6 text-muted-foreground">Loading stage history...</div>
              ) : stageRecords.length === 0 ? (
                <div className="py-10 text-center border border-dashed rounded-lg text-muted-foreground">
                  No records logged for stage {activeStage}.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Attempt Type</TableHead>
                      <TableHead>Rating</TableHead>
                      <TableHead>Decision</TableHead>
                      <TableHead>Faculty ID</TableHead>
                      <TableHead>Notes</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stageRecords.map((rec) => (
                      <TableRow key={rec.id}>
                        <TableCell>
                          <span className="flex items-center gap-1.5 text-xs">
                            <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                            {new Date(rec.signed_off_at).toLocaleDateString()}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {rec.attempt_type === "F"
                              ? "First (F)"
                              : rec.attempt_type === "R"
                              ? "Repeat (R)"
                              : "Remediation (Re)"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              rec.rating === "E"
                                ? "default"
                                : rec.rating === "M"
                                ? "secondary"
                                : "destructive"
                            }
                          >
                            {rec.rating === "E"
                              ? "Exceeds (E)"
                              : rec.rating === "M"
                              ? "Meets (M)"
                              : "Below (B)"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              rec.faculty_decision === "C"
                                ? "default"
                                : rec.faculty_decision === "R"
                                ? "secondary"
                                : "destructive"
                            }
                            className={cn(
                              rec.faculty_decision === "C"
                                ? "bg-green-600 hover:bg-green-700 text-white"
                                : rec.faculty_decision === "R"
                                ? "bg-amber-500 hover:bg-amber-600 text-white"
                                : "bg-red-500 hover:bg-red-600 text-white"
                            )}
                          >
                            {rec.faculty_decision === "C"
                              ? "Certify (C)"
                              : rec.faculty_decision === "R"
                              ? "Repeat (R)"
                              : "Remediate (Re)"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs truncate max-w-[120px]">
                          {rec.faculty_id}
                        </TableCell>
                        <TableCell className="text-xs max-w-xs break-words text-muted-foreground italic">
                          {rec.notes ? `"${rec.notes}"` : "No notes provided"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center p-12 border border-dashed rounded-lg bg-card text-center">
          <User className="h-10 w-10 text-muted-foreground mb-4" />
          <h3 className="font-semibold text-lg">No Student Context</h3>
          <p className="text-sm text-muted-foreground max-w-sm mt-1">
            Please select a student from the dropdown above to view their DOAP progression pipeline.
          </p>
        </div>
      )}
    </div>
  );
}
