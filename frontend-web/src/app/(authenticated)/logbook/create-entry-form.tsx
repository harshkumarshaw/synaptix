"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useCreateEntry } from "@/hooks/use-logbook";
import { toast } from "sonner";

const createEntrySchema = z
  .object({
    subject_code: z.string().optional(),
    elective_id: z.string().optional(),
    professional_phase: z.enum(["Phase I", "Phase II", "Phase III Part I", "Phase III Part II"]),
    competency_code: z.string().min(2, "Competency code must be at least 2 characters"),
    nmc_level: z.enum(["K", "KH", "SH", "P"]),
    is_core: z.boolean().default(false),
    activity_date: z.string().refine((val) => {
      const date = new Date(val);
      const today = new Date();
      today.setHours(23, 59, 59, 999);
      return date <= today;
    }, "Activity date cannot be in the future"),
    activity_name: z.string().min(1, "Activity name is required").max(150),
    reflection: z.string().optional(),
  })
  .refine((data) => {
    const hasSubject = !!data.subject_code;
    const hasElective = !!data.elective_id;
    return hasSubject !== hasElective;
  }, {
    message: "Specify either Subject Code or Elective ID, but not both",
    path: ["subject_code"],
  });

type CreateEntryValues = z.infer<typeof createEntrySchema>;

interface CreateEntryFormProps {
  studentId: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export function CreateEntryForm({ studentId, onSuccess, onCancel }: CreateEntryFormProps) {
  const createMutation = useCreateEntry();
  const [backdatedWarning, setBackdatedWarning] = useState(false);

  const form = useForm<any>({
    resolver: zodResolver(createEntrySchema),
    defaultValues: {
      subject_code: "",
      elective_id: "",
      professional_phase: "Phase I",
      competency_code: "",
      nmc_level: "K",
      is_core: false,
      activity_date: new Date().toISOString().split("T")[0],
      activity_name: "",
      reflection: "",
    },
  });

  const watchDate = form.watch("activity_date");

  // Check if date is backdated > 7 days ago
  const checkBackdated = (dateStr: string) => {
    if (!dateStr) return;
    const date = new Date(dateStr);
    const today = new Date();
    const diffTime = today.getTime() - date.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    setBackdatedWarning(diffDays > 7);
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    form.setValue("activity_date", e.target.value);
    checkBackdated(e.target.value);
  };

  async function onSubmit(values: CreateEntryValues) {
    try {
      const payload = {
        student_id: studentId,
        professional_phase: values.professional_phase,
        competency_code: values.competency_code,
        nmc_level: values.nmc_level,
        is_core: values.is_core,
        activity_date: values.activity_date,
        activity_name: values.activity_name,
        reflection: values.reflection || undefined,
        ...(values.subject_code ? { subject_code: values.subject_code } : {}),
        ...(values.elective_id ? { elective_id: values.elective_id } : {}),
      };

      await createMutation.mutateAsync(payload);
      toast.success("Logbook entry created successfully");
      onSuccess();
    } catch (err: any) {
      const msg = err.response?.data?.detail?.message || "Failed to create logbook entry";
      toast.error(msg);
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="subject_code">Subject Code</Label>
          <Input
            id="subject_code"
            placeholder="e.g. ANAT"
            {...form.register("subject_code")}
            disabled={!!form.watch("elective_id")}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="elective_id">Elective ID (UUID)</Label>
          <Input
            id="elective_id"
            placeholder="e.g. uuid-format-id"
            {...form.register("elective_id")}
            disabled={!!form.watch("subject_code")}
          />
        </div>
      </div>
      {form.formState.errors.subject_code && (
        <p className="text-xs text-destructive">{(form.formState.errors.subject_code.message as string)}</p>
      )}

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="professional_phase">Professional Phase</Label>
          <select
            id="professional_phase"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            {...form.register("professional_phase")}
          >
            <option value="Phase I">Phase I</option>
            <option value="Phase II">Phase II</option>
            <option value="Phase III Part I">Phase III Part I</option>
            <option value="Phase III Part II">Phase III Part II</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="competency_code">Competency Code</Label>
          <Input
            id="competency_code"
            placeholder="e.g. AN-1.1"
            {...form.register("competency_code")}
          />
          {form.formState.errors.competency_code && (
            <p className="text-xs text-destructive">{(form.formState.errors.competency_code.message as string)}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="nmc_level">NMC Level</Label>
          <select
            id="nmc_level"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            {...form.register("nmc_level")}
          >
            <option value="K">K (Knows)</option>
            <option value="KH">KH (Knows How)</option>
            <option value="SH">SH (Shows How)</option>
            <option value="P">P (Performs)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="activity_date">Activity Date</Label>
          <Input
            id="activity_date"
            type="date"
            {...form.register("activity_date")}
            onChange={handleDateChange}
          />
          {form.formState.errors.activity_date && (
            <p className="text-xs text-destructive">{(form.formState.errors.activity_date.message as string)}</p>
          )}
          {backdatedWarning && (
            <div className="text-xs text-amber-500 font-semibold bg-amber-500/10 p-2 rounded">
              ⚠️ Warning: Backdating &gt; 7 days requires HOD approval.
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="activity_name">Activity Name</Label>
          <Input
            id="activity_name"
            placeholder="e.g. Dissection of Upper Limb"
            {...form.register("activity_name")}
          />
          {form.formState.errors.activity_name && (
            <p className="text-xs text-destructive">{(form.formState.errors.activity_name.message as string)}</p>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox
          id="is_core"
          checked={form.watch("is_core")}
          onCheckedChange={(checked) => form.setValue("is_core", !!checked)}
        />
        <Label htmlFor="is_core">Core Competency</Label>
      </div>

      <div className="space-y-2">
        <Label htmlFor="reflection">Reflection</Label>
        <Textarea
          id="reflection"
          placeholder="Student reflection on the session (optional)"
          {...form.register("reflection")}
        />
      </div>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={createMutation.isPending}>
          {createMutation.isPending ? "Creating..." : "Create Draft"}
        </Button>
      </div>
    </form>
  );
}
