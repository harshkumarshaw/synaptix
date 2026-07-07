"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Play, Eye, Settings2, BarChart2, Users, CheckCircle, AlertTriangle } from "lucide-react";
import { useElectives, useRunAllocation } from "@/hooks/use-electives";
import { useToast } from "@/hooks/use-toast";
import type { AllocationRunResult, Elective } from "@/types/electives";

export function AdminAllocation() {
  const [selectedBlock, setSelectedBlock] = useState<"Block 1" | "Block 2">("Block 1");
  const [algorithm, setAlgorithm] = useState<"fcfs" | "ranked">("ranked");
  const [reallocateMode, setReallocateMode] = useState<"additive" | "full" | "none">("none");
  const [runResult, setRunResult] = useState<AllocationRunResult | null>(null);

  const { data: electives, isLoading: isElectivesLoading, refetch: refetchElectives } = useElectives(selectedBlock);
  const runAllocation = useRunAllocation();
  const { toast } = useToast();

  // Extract unique curriculum IDs from electives list
  const curriculumIds = Array.from(new Set(electives?.map((e) => e.curriculum_id) ?? []));
  const [selectedCurriculum, setSelectedCurriculum] = useState<string>("");

  // Default to first curriculum ID when loaded
  if (curriculumIds.length > 0 && !selectedCurriculum) {
    setSelectedCurriculum(curriculumIds[0]);
  }

  async function executeAllocation(dryRun: boolean) {
    if (!selectedCurriculum) {
      toast({
        title: "Configuration Error",
        description: "Please select a valid curriculum.",
        variant: "destructive",
      });
      return;
    }

    const payload = {
      curriculum_id: selectedCurriculum,
      block: selectedBlock,
      algorithm,
      dry_run: dryRun,
      force_reallocate: reallocateMode === "none" ? null : reallocateMode,
    };

    runAllocation.mutate(payload, {
      onSuccess: (data: any) => {
        setRunResult(data);
        refetchElectives();
        toast({
          title: dryRun ? "Dry Run Complete" : "Allocation Complete",
          description: dryRun
            ? "Dry run calculated successfully. No database writes were committed."
            : "Live allocation run successfully committed to database.",
        });
      },
      onError: (err: any) => {
        toast({
          title: "Allocation Failed",
          description: err.response?.data?.detail?.message || err.response?.data?.detail || "Could not complete allocation.",
          variant: "destructive",
        });
      },
    });
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Electives Allocation Engine</h1>
        <p className="text-muted-foreground text-sm">
          Run allocation algorithms to assign students to curriculum electives based on preference rank and submission order.
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-5">
        {/* Left Side: Configuration panel (2/5 width) */}
        <Card className="lg:col-span-2 border-primary/10 shadow-lg bg-background/80 backdrop-blur-md">
          <CardHeader className="border-b pb-4">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Settings2 className="h-5 w-5 text-primary" />
              Run Configuration
            </CardTitle>
            <CardDescription>Specify parameters for the elective allocation run</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-6">
            {/* Curriculum Selector */}
            <div className="space-y-2">
              <label className="text-sm font-semibold">Target Curriculum</label>
              {isElectivesLoading ? (
                <div className="h-10 bg-muted animate-pulse rounded-md" />
              ) : (
                <select
                  value={selectedCurriculum}
                  onChange={(e) => setSelectedCurriculum(e.target.value)}
                  className="w-full h-10 px-3 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  {curriculumIds.map((id) => (
                    <option key={id} value={id}>
                      Curriculum {id.slice(0, 8)}
                    </option>
                  ))}
                  {curriculumIds.length === 0 && (
                    <option value="">No curriculum found in available electives</option>
                  )}
                </select>
              )}
            </div>

            {/* Block Selector */}
            <div className="space-y-2">
              <label className="text-sm font-semibold">Active Block</label>
              <div className="flex gap-2">
                <Button
                  variant={selectedBlock === "Block 1" ? "default" : "outline"}
                  onClick={() => setSelectedBlock("Block 1")}
                  className="flex-1 rounded-lg"
                >
                  Block 1
                </Button>
                <Button
                  variant={selectedBlock === "Block 2" ? "default" : "outline"}
                  onClick={() => setSelectedBlock("Block 2")}
                  className="flex-1 rounded-lg"
                >
                  Block 2
                </Button>
              </div>
            </div>

            {/* Algorithm Selector */}
            <div className="space-y-2">
              <label className="text-sm font-semibold">Allocation Algorithm</label>
              <div className="grid grid-cols-2 gap-4">
                <div
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                    algorithm === "ranked"
                      ? "border-primary bg-primary/5 text-primary"
                      : "hover:bg-muted/40"
                  }`}
                  onClick={() => setAlgorithm("ranked")}
                >
                  <input
                    type="radio"
                    checked={algorithm === "ranked"}
                    readOnly
                    className="accent-primary"
                  />
                  <div className="text-sm font-medium">Ranked Choice</div>
                </div>
                <div
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                    algorithm === "fcfs"
                      ? "border-primary bg-primary/5 text-primary"
                      : "hover:bg-muted/40"
                  }`}
                  onClick={() => setAlgorithm("fcfs")}
                >
                  <input
                    type="radio"
                    checked={algorithm === "fcfs"}
                    readOnly
                    className="accent-primary"
                  />
                  <div className="text-sm font-medium">FCFS</div>
                </div>
              </div>
            </div>

            {/* Reallocate Mode */}
            <div className="space-y-2">
              <label className="text-sm font-semibold">Reallocation Mode</label>
              <select
                value={reallocateMode}
                onChange={(e) => setReallocateMode(e.target.value as any)}
                className="w-full h-10 px-3 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="none">Additive Only (Unallocated students only)</option>
                <option value="additive">Additive Overwrite (Preserve prior but run leftovers)</option>
                <option value="full">Full Reallocate (Clear existing allocations first!)</option>
              </select>
            </div>

            {/* Actions */}
            <div className="flex gap-4 pt-4 border-t">
              <Button
                variant="outline"
                className="flex-1 gap-2 rounded-lg font-medium"
                onClick={() => executeAllocation(true)}
                disabled={runAllocation.isPending}
              >
                <Eye className="h-4 w-4" />
                Dry Run
              </Button>
              <Button
                className="flex-1 gap-2 rounded-lg font-medium"
                onClick={() => executeAllocation(false)}
                disabled={runAllocation.isPending}
              >
                <Play className="h-4 w-4" />
                {runAllocation.isPending ? "Executing..." : "Run Live"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Right Side: Results & Capacities (3/5 width) */}
        <div className="lg:col-span-3 space-y-6">
          {/* Results Overview */}
          {runResult && (
            <Card className="border-primary/10 shadow-lg bg-background/80">
              <CardHeader className="border-b pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg font-semibold flex items-center gap-2">
                      <BarChart2 className="h-5 w-5 text-primary" />
                      Allocation Results
                    </CardTitle>
                    <CardDescription>
                      {runResult.dry_run ? "Simulation preview (Dry Run)" : "Live Run Results"}
                    </CardDescription>
                  </div>
                  <Badge variant={runResult.dry_run ? "secondary" : "default"}>
                    {runResult.dry_run ? "Simulation" : "Committed"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 border rounded-xl bg-card">
                    <div className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                      <Users className="h-3.5 w-3.5" />
                      Total Considered
                    </div>
                    <div className="text-2xl font-bold mt-1">{runResult.total_students_considered}</div>
                  </div>
                  <div className="p-4 border rounded-xl bg-card">
                    <div className="text-xs font-semibold text-emerald-500 flex items-center gap-1.5">
                      <CheckCircle className="h-3.5 w-3.5" />
                      Total Allocated
                    </div>
                    <div className="text-2xl font-bold text-emerald-500 mt-1">{runResult.total_allocated}</div>
                  </div>
                  <div className={`p-4 border rounded-xl ${
                    runResult.total_unallocated_pending_review > 0
                      ? "bg-red-500/10 border-red-500/20 text-red-500"
                      : "bg-card"
                  }`}>
                    <div className="text-xs font-semibold flex items-center gap-1.5">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Pending Review
                    </div>
                    <div className="text-2xl font-bold mt-1">{runResult.total_unallocated_pending_review}</div>
                  </div>
                </div>

                {/* Rank Distribution */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold">Allocations by Rank Choice</h4>
                  <div className="grid grid-cols-5 gap-2 text-center">
                    {Object.entries(runResult.allocations_by_rank ?? {}).slice(0, 5).map(([rank, count]) => (
                      <div key={rank} className="p-2 border rounded bg-muted/30">
                        <div className="text-[10px] font-bold text-muted-foreground capitalize">
                          {rank.replace("_", " ")}
                        </div>
                        <div className="text-sm font-bold mt-0.5">{count}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Electives Capacity Utilization */}
          <Card className="border-primary/10 shadow-lg bg-background/80">
            <CardHeader className="border-b pb-4">
              <CardTitle className="text-lg font-semibold">Capacity Utilization</CardTitle>
              <CardDescription>Allocated seats per elective in {selectedBlock}</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-4 max-h-[400px] overflow-y-auto">
              {isElectivesLoading ? (
                <div className="space-y-4">
                  <div className="h-12 bg-muted animate-pulse rounded-lg" />
                  <div className="h-12 bg-muted animate-pulse rounded-lg" />
                  <div className="h-12 bg-muted animate-pulse rounded-lg" />
                </div>
              ) : (
                electives?.map((elective) => {
                  const percent = (elective.allocated_count / elective.capacity) * 100;
                  return (
                    <div key={elective.id} className="space-y-1.5 p-3 border rounded-xl bg-card">
                      <div className="flex items-center justify-between">
                        <div className="min-w-0 pr-4">
                          <p className="text-sm font-semibold truncate">{elective.title}</p>
                          <p className="text-xs text-muted-foreground">Code: {elective.code}</p>
                        </div>
                        <div className="text-xs font-bold text-right shrink-0">
                          {elective.allocated_count} / {elective.capacity} filled
                        </div>
                      </div>
                      <Progress value={percent} className="h-2" />
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
