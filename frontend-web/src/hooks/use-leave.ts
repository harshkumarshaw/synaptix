import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { LeaveRequest, LeaveRequestCreate } from "@/types/leave";

export function useLeaveRequests(filters?: {
  student_id?: string;
  leave_status?: string;
}) {
  return useQuery({
    queryKey: ["leave", "requests", filters],
    queryFn: async () => {
      const { data } = await api.get<LeaveRequest[]>("/leave/requests", {
        params: filters,
      });
      return data;
    },
  });
}

export function useCreateLeave() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LeaveRequestCreate) => {
      const { data } = await api.post<LeaveRequest>("/leave/requests", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leave", "requests"] });
    },
  });
}

export function useApproveLeave() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, remarks }: { id: string; remarks: string }) => {
      const { data } = await api.post<LeaveRequest>(
        `/leave/requests/${id}/approve`,
        {
          remarks,
        },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leave", "requests"] });
    },
  });
}

export function useRejectLeave() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, remarks }: { id: string; remarks: string }) => {
      const { data } = await api.post<LeaveRequest>(
        `/leave/requests/${id}/reject`,
        {
          remarks,
        },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leave", "requests"] });
    },
  });
}

export function useCancelLeave() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<LeaveRequest>(
        `/leave/requests/${id}/cancel`,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leave", "requests"] });
    },
  });
}

export function useLeaveImpactPreview(id: string) {
  return useQuery({
    queryKey: ["leave", "impact", id],
    queryFn: async () => {
      try {
        const { data } = await api.get(`/leave/requests/${id}/impact-preview`);
        return data;
      } catch (err: any) {
        if (err.response?.status === 404) {
          return null; // Gracefully return null if endpoint doesn't exist
        }
        throw err;
      }
    },
    enabled: !!id,
    retry: false,
  });
}
