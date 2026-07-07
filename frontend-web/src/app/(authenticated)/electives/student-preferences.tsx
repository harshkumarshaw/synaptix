"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { GripVertical, ArrowUp, ArrowDown, Sparkles, CheckCircle2, AlertCircle } from "lucide-react";
import { useElectives, useMyPreferences, useSubmitPreferences } from "@/hooks/use-electives";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/stores/auth-store";
import type { Elective } from "@/types/electives";

export function StudentPreferences() {
  const [activeBlock, setActiveBlock] = useState<"Block 1" | "Block 2">("Block 1");
  const user = useAuthStore((state) => state.user);
  const studentId = user?.student_id || user?.id || "";

  const { data: electives, isLoading: isElectivesLoading } = useElectives(activeBlock);
  const { data: existing, isLoading: isPrefsLoading } = useMyPreferences(studentId, activeBlock);
  const submitPrefs = useSubmitPreferences();
  const { toast } = useToast();

  const [ranked, setRanked] = useState<string[]>([]);

  // Reset/Initialize ranked list when existing preferences load or block changes
  useEffect(() => {
    if (existing) {
      // Sort existing by rank_position
      const sorted = [...existing].sort((a, b) => a.rank_position - b.rank_position);
      setRanked(sorted.map((p) => p.elective_id));
    } else {
      setRanked([]);
    }
  }, [existing, activeBlock]);

  function moveUp(index: number) {
    if (index === 0) return;
    const next = [...ranked];
    [next[index - 1], next[index]] = [next[index], next[index - 1]];
    setRanked(next);
  }

  function moveDown(index: number) {
    if (index === ranked.length - 1) return;
    const next = [...ranked];
    [next[index], next[index + 1]] = [next[index + 1], next[index]];
    setRanked(next);
  }

  function addToRanking(electiveId: string) {
    if (ranked.includes(electiveId)) return;
    setRanked([...ranked, electiveId]);
  }

  function removeFromRanking(electiveId: string) {
    setRanked(ranked.filter((id) => id !== electiveId));
  }

  async function handleSubmit() {
    if (!studentId) return;
    const preferences = ranked.map((electiveId, i) => ({
      elective_id: electiveId,
      rank_position: i + 1,
    }));

    submitPrefs.mutate(
      {
        student_id: studentId,
        block: activeBlock,
        preferences,
      },
      {
        onSuccess: () => {
          toast({
            title: "Success",
            description: "Your elective preferences have been submitted successfully.",
          });
        },
        onError: (err: any) => {
          toast({
            title: "Submission Failed",
            description: err.response?.data?.detail || "Could not save preferences.",
            variant: "destructive",
          });
        },
      }
    );
  }

  const rankedElectives = ranked
    .map((id) => electives?.find((e) => e.id === id))
    .filter(Boolean) as Elective[];

  const unranked = electives?.filter((e) => !ranked.includes(e.id)) ?? [];

  const isSaved = existing && existing.length > 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Banner / Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 bg-gradient-to-r from-primary/10 via-background to-secondary/10 border rounded-2xl backdrop-blur-md relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-1/4 -translate-y-1/4 w-72 h-72 rounded-full bg-primary/5 blur-3xl" />
        <div className="space-y-1 relative z-10">
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-extrabold tracking-tight">Electives Portal</h1>
            <Sparkles className="h-5 w-5 text-yellow-500 animate-pulse" />
          </div>
          <p className="text-muted-foreground text-sm max-w-md">
            Rank your preferred electives. NMC CBME mandates separate clinical/non-clinical choices across blocks.
          </p>
        </div>
        <div className="flex items-center gap-2 relative z-10 bg-background/60 p-1 rounded-xl border backdrop-blur-md self-start sm:self-center">
          <Button
            variant={activeBlock === "Block 1" ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveBlock("Block 1")}
            className="rounded-lg font-medium transition-all"
          >
            Block 1
          </Button>
          <Button
            variant={activeBlock === "Block 2" ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveBlock("Block 2")}
            className="rounded-lg font-medium transition-all"
          >
            Block 2
          </Button>
        </div>
      </div>

      {isSaved && (
        <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 dark:text-emerald-400 rounded-xl">
          <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
          <div className="text-sm font-medium">
            Preferences for {activeBlock} are saved. You can adjust and resubmit them at any time before the allocation run starts.
          </div>
        </div>
      )}

      {isElectivesLoading || isPrefsLoading ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="h-[400px] animate-pulse bg-muted/40" />
          <Card className="h-[400px] animate-pulse bg-muted/40" />
        </div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-5">
          {/* Left Column: Ranked List (3/5 width) */}
          <Card className="lg:col-span-3 border-primary/10 shadow-lg bg-background/80 backdrop-blur-md">
            <CardHeader className="border-b pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-semibold flex items-center gap-2">
                    My Choice Sequence
                  </CardTitle>
                  <CardDescription>Drag or use arrows to define order of preference</CardDescription>
                </div>
                <Badge variant={rankedElectives.length > 0 ? "default" : "secondary"}>
                  {rankedElectives.length} Selected
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              {rankedElectives.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center border-2 border-dashed rounded-xl p-6 bg-muted/20">
                  <AlertCircle className="h-10 w-10 text-muted-foreground/60 mb-3" />
                  <p className="text-sm font-medium text-muted-foreground">
                    Your choice list is empty.
                  </p>
                  <p className="text-xs text-muted-foreground max-w-xs mt-1">
                    Select electives from the available catalog on the right to build your preference ranking.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {rankedElectives.map((elective, i) => (
                    <div
                      key={elective.id}
                      className="group flex items-center gap-3 rounded-xl border p-4 bg-card hover:bg-muted/30 hover:border-primary/20 transition-all duration-200"
                    >
                      <GripVertical className="h-5 w-5 text-muted-foreground/40 group-hover:text-muted-foreground/80 cursor-grab active:cursor-grabbing transition-colors" />
                      <Badge
                        variant="outline"
                        className="w-7 h-7 flex items-center justify-center p-0 rounded-full font-bold text-xs bg-muted"
                      >
                        {i + 1}
                      </Badge>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold truncate">{elective.title}</p>
                        <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
                          <span className="capitalize px-1.5 py-0.5 rounded bg-muted/60 text-muted-foreground border">
                            {elective.elective_type.replace("_", " ")}
                          </span>
                          <span>· Code: {elective.code}</span>
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => moveUp(i)}
                          disabled={i === 0}
                          className="h-8 w-8 hover:bg-primary/10 hover:text-primary transition-colors"
                        >
                          <ArrowUp className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => moveDown(i)}
                          disabled={i === rankedElectives.length - 1}
                          className="h-8 w-8 hover:bg-primary/10 hover:text-primary transition-colors"
                        >
                          <ArrowDown className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeFromRanking(elective.id)}
                          className="h-8 w-8 text-destructive/70 hover:text-destructive hover:bg-destructive/10 transition-colors"
                        >
                          ✕
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <Button
                className="w-full mt-6 py-6 font-semibold text-base transition-transform hover:-translate-y-0.5 active:translate-y-0"
                onClick={handleSubmit}
                disabled={ranked.length === 0 || submitPrefs.isPending}
              >
                {submitPrefs.isPending ? "Submitting Choices..." : `Submit Ranking List`}
              </Button>
            </CardContent>
          </Card>

          {/* Right Column: Catalog (2/5 width) */}
          <Card className="lg:col-span-2 border-primary/10 shadow-lg bg-background/85">
            <CardHeader className="border-b pb-4">
              <div>
                <CardTitle className="text-lg font-semibold">Available Electives</CardTitle>
                <CardDescription>Select electives to add to your rankings</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="pt-6 max-h-[500px] overflow-y-auto space-y-3">
              {unranked.length === 0 ? (
                <div className="text-center py-12 text-sm text-muted-foreground font-medium">
                  All available electives added to your sequence list.
                </div>
              ) : (
                unranked.map((elective) => (
                  <div
                    key={elective.id}
                    onClick={() => addToRanking(elective.id)}
                    className="group flex items-center justify-between border rounded-xl p-4 bg-card/60 hover:bg-primary/5 hover:border-primary/10 cursor-pointer transition-all duration-200"
                  >
                    <div className="min-w-0 pr-4">
                      <p className="text-sm font-semibold truncate group-hover:text-primary transition-colors">
                        {elective.title}
                      </p>
                      <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-1">
                        <span className="capitalize px-1 py-0.5 rounded bg-muted text-muted-foreground border">
                          {elective.elective_type.replace("_", " ")}
                        </span>
                        <span>· Cap: {elective.capacity}</span>
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="group-hover:bg-primary group-hover:text-primary-foreground group-hover:border-primary shrink-0 transition-colors"
                    >
                      + Add
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
