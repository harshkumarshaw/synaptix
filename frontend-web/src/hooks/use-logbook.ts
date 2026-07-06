import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  LogbookEntry,
  LogbookEntryCreate,
  LogbookSignoff,
  LogbookSubmit,
  IAAssessment,
} from "@/types/logbook";

export function useStudentEntries(studentId: string, filters?: Record<string, any>) {
  return useQuery({
    queryKey: ["logbook", "entries", studentId, filters],
    queryFn: async () => {
      const { data } = await api.get<LogbookEntry[]>("/logbook/entries", {
        params: { student_id: studentId, ...filters },
      });
      return data;
    },
    enabled: !!studentId,
  });
}

export function useCreateEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LogbookEntryCreate) => {
      const { data } = await api.post<LogbookEntry>("/logbook/entries", payload);
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["logbook", "entries"] });
    },
  });
}

export function useSubmitEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ entryId, payload }: { entryId: string; payload: LogbookSubmit }) => {
      const { data } = await api.patch<LogbookEntry>(`/logbook/entries/${entryId}/submit`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["logbook", "entries"] });
    },
  });
}

export function useSignoffEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ entryId, payload }: { entryId: string; payload: LogbookSignoff }) => {
      const { data } = await api.patch<LogbookEntry>(`/logbook/entries/${entryId}/signoff`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["logbook", "entries"] });
    },
  });
}

export function useIAAssessment(studentId: string, subjectCode: string, phase: string) {
  return useQuery({
    queryKey: ["logbook", "assessment", studentId, subjectCode, phase],
    queryFn: async () => {
      const { data } = await api.get<IAAssessment>(
        `/logbook/assessments/${studentId}/${subjectCode}/${phase}`
      );
      return data;
    },
    enabled: !!studentId && !!subjectCode && !!phase,
  });
}

export function useStudents() {
  return useQuery({
    queryKey: ["students"],
    queryFn: async () => {
      const { data } = await api.get<any[]>("/institution/students");
      return data;
    },
  });
}

