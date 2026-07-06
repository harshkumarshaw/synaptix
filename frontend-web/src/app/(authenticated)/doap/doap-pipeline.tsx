"use client";

import { Fragment } from "react";
import type { DoapState } from "@/types/doap";
import { cn } from "@/lib/utils";

const STAGES = ["D", "O", "A", "P"] as const;
const STAGE_LABELS = {
  D: "Demonstration",
  O: "Observation",
  A: "Assistance",
  P: "Performance",
};

interface DoapPipelineProps {
  state: DoapState;
  activeStage: string | null;
  onStageClick: (stage: string) => void;
}

export function DoapPipeline({ state, activeStage, onStageClick }: DoapPipelineProps) {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-card border shadow-xs max-w-2xl mx-auto">
      {STAGES.map((stage, i) => {
        const isCertified = state.certified_stages.includes(stage);
        const isCurrent = state.pending_stage === stage;
        const count = state.records_per_stage[stage] || 0;
        const isActive = activeStage === stage;

        const colorClass = isCertified
          ? "bg-green-500 text-white shadow-green-500/20"
          : isCurrent
          ? "bg-blue-500 text-white shadow-blue-500/20"
          : "bg-zinc-200 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-600";

        return (
          <Fragment key={stage}>
            {/* Connection Line */}
            {i > 0 && (
              <div className="hidden sm:block h-0.5 flex-1 bg-zinc-200 dark:bg-zinc-800 mx-2">
                <div
                  className={cn(
                    "h-full bg-green-500 transition-all duration-300",
                    state.certified_stages.includes(STAGES[i - 1]) ? "w-full" : "w-0"
                  )}
                />
              </div>
            )}

            {/* Stage Node */}
            <div
              onClick={() => onStageClick(stage)}
              className={cn(
                "flex flex-col items-center cursor-pointer transition-all duration-200 hover:scale-105",
                isActive ? "ring-2 ring-primary ring-offset-2" : ""
              )}
            >
              <div className={cn("h-12 w-12 rounded-full flex items-center justify-center text-base font-bold shadow-md transition-all duration-300", colorClass)}>
                {stage}
              </div>
              <p className="text-xs font-semibold mt-2 text-foreground">{STAGE_LABELS[stage]}</p>
              <p className="text-[10px] text-muted-foreground">{count} record(s)</p>
              <p className="text-[10px] font-medium mt-1">
                {isCertified ? (
                  <span className="text-green-600">✓ Certified</span>
                ) : isCurrent ? (
                  <span className="text-blue-500">● Current</span>
                ) : (
                  <span className="text-muted-foreground">○ Locked</span>
                )}
              </p>
            </div>
          </Fragment>
        );
      })}
    </div>
  );
}
export { STAGES, STAGE_LABELS };
