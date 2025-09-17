import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  createStrategyVersionStrategiesPost,
  getStrategiesStrategiesGet,
  type GetStrategiesStrategiesGetParams,
  type StrategyCreate,
} from "@/openapi";
import { useMutation, useQuery } from "@tanstack/react-query";

export function useStrategiesQuery(params?: GetStrategiesStrategiesGetParams) {
  return useQuery({
    queryKey: queryKeys.strategies(params),
    queryFn: async () => handleApi(await getStrategiesStrategiesGet(params)),
  });
}

export function useCreateStrategyMutation() {
  return useMutation({
    mutationFn: async (params: StrategyCreate) =>
      handleApi(await createStrategyVersionStrategiesPost(params)),
  });
}
