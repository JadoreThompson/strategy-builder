import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  createStrategyVersionStrategiesPost,
  deleteStrategyStrategiesStrategyIdDelete,
  getStrategiesStrategiesGet,
  type GetStrategiesStrategiesGetParams,
  type StrategyCreate,
} from "@/openapi";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useStrategiesQuery(params?: GetStrategiesStrategiesGetParams) {
  return useQuery({
    queryKey: queryKeys.strategies(params),
    queryFn: async () => handleApi(await getStrategiesStrategiesGet(params)),
  });
}

export function useCreateStrategyMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: StrategyCreate) =>
      handleApi(await createStrategyVersionStrategiesPost(data)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.strategies() });
    },
  });
}

export function useDeleteStrategyMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (strategyId: string) =>
      handleApi(await deleteStrategyStrategiesStrategyIdDelete(strategyId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.strategies() });
    },
  });
}
