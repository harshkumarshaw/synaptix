import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { DashboardStats } from "@/types/attendance";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: async (): Promise<DashboardStats> => {
      try {
        const { data } = await api.get<DashboardStats>("/dashboard/stats");
        return data;
      } catch {
        // Endpoint may not exist yet — return placeholder
        return {
          total_students: 0,
          todays_attendance_rate: 0,
          pending_logbook_reviews: 0,
          at_risk_students: 0,
        };
      }
    },
    staleTime: 60_000, // refresh every minute
  });
}
