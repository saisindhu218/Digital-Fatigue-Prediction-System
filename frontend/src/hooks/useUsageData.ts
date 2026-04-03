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
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true
  });
}