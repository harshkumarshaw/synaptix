import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { DoapRecord, DoapState } from "@/types/doap";

export function useDoapRecords(studentId: string, competencyCode?: string) {
  return useQuery({
    queryKey: ["doap", "records", studentId, competencyCode],
    queryFn: async () => {
      const { data } = await api.get<DoapRecord[]>(
        `/doap/student/${studentId}`,
        {
          params: { competency_code: competencyCode },
        },
      );
      return data;
    },
    enabled: !!studentId,
  });
}

export function useDoapState(studentId: string, competencyCode: string) {
  return useQuery({
    queryKey: ["doap", "state", studentId, competencyCode],
    queryFn: async () => {
      const { data } = await api.get<DoapState>(
        `/doap/student/${studentId}/competency/${competencyCode}/state`,
      );
      return data;
    },
    enabled: !!studentId && !!competencyCode,
  });
}
