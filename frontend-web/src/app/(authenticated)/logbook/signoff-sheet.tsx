"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useSignoffEntry } from "@/hooks/use-logbook";
import { LogbookEntry } from "@/types/logbook";
import { toast } from "sonner";
import { useEffect } from "react";

const signoffSchema = z
  .object({
    rating: z.enum(["B", "M", "E"]),
    faculty_decision: z.enum(["C", "R", "Re"]),
    faculty_initials: z.string().min(1, "Initials are required").max(10),
    feedback: z.string().optional(),
  })
  .refine(
    (data) => {
      // Rating B + Decision C is blocked
      if (data.rating === "B" && data.faculty_decision === "C") {
        return false;
      }
      return true;
    },
    {
      message:
        "Rating Below Expectation (B) cannot be Certified (C). Select Repeat or Remediate.",
      path: ["faculty_decision"],
    },
  );

type SignoffValues = z.infer<typeof signoffSchema>;

interface SignoffSheetProps {
  entry: LogbookEntry | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function SignoffSheet({
  entry,
  isOpen,
  onClose,
  onSuccess,
}: SignoffSheetProps) {
  const signoffMutation = useSignoffEntry();

  const form = useForm<SignoffValues>({
    resolver: zodResolver(signoffSchema),
    defaultValues: {
      rating: "M",
      faculty_decision: "C",
      faculty_initials: "",
      feedback: "",
    },
  });

  const rating = form.watch("rating");
  const decision = form.watch("faculty_decision");

  // Reset form when entry changes
  useEffect(() => {
    if (entry) {
      form.reset({
        rating: "M",
        faculty_decision: "C",
        faculty_initials: "",
        feedback: "",
      });
    }
  }, [entry, form]);

  if (!entry) return null;

  async function onSubmit(values: SignoffValues) {
    if (!entry) return;
    try {
      await signoffMutation.mutateAsync({
        entryId: entry.id,
        payload: {
          rating: values.rating,
          faculty_decision: values.faculty_decision,
          faculty_initials: values.faculty_initials,
          feedback: values.feedback,
        },
      });
      toast.success("Logbook entry signed off successfully");
      onSuccess();
    } catch (err: any) {
      const msg =
        err.response?.data?.detail?.message || "Failed to submit signoff";
      toast.error(msg);
    }
  }

  // Check custom validation for disabled state
  const isBlocked = rating === "B" && decision === "C";

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Signoff Logbook Entry</SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Read-only Entry Details */}
          <div className="rounded-lg bg-muted p-4 space-y-3 text-sm">
            <h3 className="font-semibold text-base">Entry Details</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-muted-foreground block">
                  Subject Code
                </span>
                <span className="font-medium">
                  {entry.subject_code || "N/A (Elective)"}
                </span>
              </div>
              {entry.elective_id && (
                <div>
                  <span className="text-muted-foreground block">
                    Elective ID
                  </span>
                  <span className="font-medium truncate block">
                    {entry.elective_id}
                  </span>
                </div>
              )}
              <div>
                <span className="text-muted-foreground block">Competency</span>
                <span className="font-medium">
                  {entry.competency_code} ({entry.nmc_level})
                </span>
              </div>
              <div>
                <span className="text-muted-foreground block">Date</span>
                <span className="font-medium">{entry.activity_date}</span>
              </div>
              <div className="col-span-2">
                <span className="text-muted-foreground block">
                  Activity Name
                </span>
                <span className="font-medium">{entry.activity_name}</span>
              </div>
              {entry.reflection && (
                <div className="col-span-2">
                  <span className="text-muted-foreground block">
                    Student Reflection
                  </span>
                  <p className="mt-1 bg-background p-2 rounded text-muted-foreground break-words italic">
                    "{entry.reflection}"
                  </p>
                </div>
              )}
            </div>
          </div>

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* Rating Selector */}
            <div className="space-y-2">
              <Label>Rating</Label>
              <div className="flex gap-4">
                <label className="flex items-center space-x-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    value="B"
                    {...form.register("rating")}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span>Below (B)</span>
                </label>
                <label className="flex items-center space-x-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    value="M"
                    {...form.register("rating")}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span>Meets (M)</span>
                </label>
                <label className="flex items-center space-x-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    value="E"
                    {...form.register("rating")}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span>Exceeds (E)</span>
                </label>
              </div>
            </div>

            {/* Decision Selector */}
            <div className="space-y-2">
              <Label>Faculty Decision</Label>
              <div className="flex gap-4">
                <label className="flex items-center space-x-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    value="C"
                    {...form.register("faculty_decision")}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span>Certify (C)</span>
                </label>
                <label className="flex items-center space-x-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    value="R"
                    {...form.register("faculty_decision")}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span>Repeat (R)</span>
                </label>
                <label className="flex items-center space-x-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    value="Re"
                    {...form.register("faculty_decision")}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span>Remediate (Re)</span>
                </label>
              </div>
              {form.formState.errors.faculty_decision && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.faculty_decision.message}
                </p>
              )}
              {isBlocked && (
                <p className="text-xs text-destructive font-semibold">
                  ⚠️ Validation Error: Cannot Certify (C) with Rating Below (B).
                </p>
              )}
            </div>

            {/* Initials */}
            <div className="space-y-2">
              <Label htmlFor="faculty_initials">Faculty Initials</Label>
              <Input
                id="faculty_initials"
                placeholder="e.g. JS"
                {...form.register("faculty_initials")}
              />
              {form.formState.errors.faculty_initials && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.faculty_initials.message}
                </p>
              )}
            </div>

            {/* Feedback */}
            <div className="space-y-2">
              <Label htmlFor="feedback">Feedback / Comments</Label>
              <Textarea
                id="feedback"
                placeholder="Provide details for repetition or remediation if applicable..."
                {...form.register("feedback")}
              />
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1"
                disabled={signoffMutation.isPending || isBlocked}
              >
                {signoffMutation.isPending
                  ? "Submitting..."
                  : decision === "C"
                    ? "Certify"
                    : "Request Revision"}
              </Button>
            </div>
          </form>
        </div>
      </SheetContent>
    </Sheet>
  );
}
