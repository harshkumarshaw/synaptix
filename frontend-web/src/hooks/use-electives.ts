import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  Elective,
  ElectivePreference,
  ElectiveAllocation,
  AllocationRunRequest,
  AllocationRunResult,
} from "@/types/electives";

export function useElectives(block?: "Block 1" | "Block 2") {
  return useQuery({
    queryKey: ["electives", "list", block],
    queryFn: async () => {
      const { data } = await api.get<Elective[]>("/electives", {
        params: block ? { block } : {},
      });
      return data;
    },
  });
}

export function useMyPreferences(studentId: string, block?: "Block 1" | "Block 2") {
  return useQuery({
    queryKey: ["electives", "preferences", studentId, block],
    queryFn: async () => {
      const { data } = await api.get<any[]>(`/electives/preferences/${studentId}`, {
        params: block ? { block } : {},
      });
      return data;
    },
    enabled: !!studentId,
  });
}

export function useSubmitPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      student_id: string;
      block: "Block 1" | "Block 2";
      preferences: ElectivePreference[];
    }) => {
      const { data } = await api.post("/electives/preferences", payload);
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["electives", "preferences", variables.student_id],
      });
    },
  });
}

export function useRunAllocation() {
  return useMutation({
    mutationFn: async (payload: AllocationRunRequest) => {
      const { data } = await api.post<AllocationRunResult>("/electives/allocate", payload);
      return data;
    },
  });
}

export function useMyAllocations(studentId: string, block?: "Block 1" | "Block 2") {
  return useQuery({
    queryKey: ["electives", "allocations", studentId, block],
    queryFn: async () => {
      const { data } = await api.get<ElectiveAllocation[]>(`/electives/allocations/${studentId}`, {
        params: block ? { block } : {},
      });
      return data;
    },
    enabled: !!studentId,
  });
}
