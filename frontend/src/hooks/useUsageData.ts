import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { UsageResponse } from "@/lib/types";

export function useUsageData(){

  const { user } = useAuth();

  return useQuery<UsageResponse>({
    queryKey:["usage",user?.id],
    enabled:!!user?.id,

    queryFn:async()=>{
      if(!user?.id) throw new Error("User not found");

      const res = await api.getUsageData(user.id);

      return res;
    },

    staleTime:30000,
    refetchInterval:15000
  });
}