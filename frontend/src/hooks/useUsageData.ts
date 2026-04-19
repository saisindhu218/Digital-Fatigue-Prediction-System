import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { UsageResponse } from "@/lib/types";

export function useUsageData() {

  const { user } = useAuth();

  return useQuery<any>({
    queryKey: ["usage", user?.id],
    enabled: !!user?.id,

    queryFn: async () => {
      if (!user?.id) {
        throw new Error("User not available");
      }

      const usage = await api.getUsageData(user.id);
      const trends = await api.getTrends(user.id);
      const analytics = await api.getAnalytics(user.id); // 🔥 NEW

      // attach trends safely
      return {
        ...usage,
        trends,
        analytics
      } as UsageResponse;
    },

    staleTime: 0,
    refetchInterval: 15000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true
  });
}

export function useTrends(days: number = 7, offsetDays: number = 0) {
  const { user } = useAuth();

  return useQuery<any>({
    queryKey: ["trends", user?.id, days, offsetDays],
    enabled: !!user?.id,
    queryFn: async () => {
      if (!user?.id) {
        throw new Error("User not available");
      }
      return api.getTrends(user.id, days, offsetDays);
    },
    staleTime: 0,
    refetchInterval: 15000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true
  });
}
