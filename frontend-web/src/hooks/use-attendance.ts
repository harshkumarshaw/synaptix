import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  AttendanceSummary,
  EventRoster,
  BulkMarkRequest,
  ExamEligibility,
  TodayEvent,
} from "@/types/attendance";

// Student: my attendance summary
export function useStudentSummary(studentId: string) {
  return useQuery({
    queryKey: ["attendance", "summary", studentId],
    queryFn: async () => {
      const { data } = await api.get<AttendanceSummary[]>(
        `/attendance/student/${studentId}/summary`,
      );
      return data;
    },
    enabled: !!studentId,
  });
}

// Faculty: event roster (who's in today's class)
export function useEventRoster(eventId: string) {
  return useQuery({
    queryKey: ["attendance", "event", eventId],
    queryFn: async () => {
      const { data } = await api.get<EventRoster>(
        `/attendance/event/${eventId}`,
      );
      return data;
    },
    enabled: !!eventId,
  });
}

// Faculty: mark attendance (bulk)
export function useBulkMark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: BulkMarkRequest) => {
      const { data } = await api.post("/attendance/mark-bulk", request);
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["attendance", "event", variables.event_id],
      });
    },
  });
}

// Student: exam eligibility
export function useExamEligibility(studentId: string, courseId: string) {
  return useQuery({
    queryKey: ["attendance", "eligibility", studentId, courseId],
    queryFn: async () => {
      const { data } = await api.get<ExamEligibility>(
        `/attendance/eligibility/${studentId}/${courseId}`,
      );
      return data;
    },
    enabled: !!studentId && !!courseId,
  });
}

// Faculty: today's events
export function useTodayEvents() {
  return useQuery({
    queryKey: ["events", "today"],
    queryFn: async () => {
      const { data } = await api.get<TodayEvent[]>("/events/today");
      return data;
    },
    retry: false,
  });
}
