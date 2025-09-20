import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  createStrategyVersionStrategiesPost,
  deleteStrategyStrategiesStrategyIdDelete,
  getStrategiesStrategiesGet,
  type GetStrategiesStrategiesGetParams,
  type StrategyCreate,
} from "@/openapi";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

export function useStrategiesQuery(params?: GetStrategiesStrategiesGetParams) {
  return useQuery({
    queryKey: queryKeys.strategies(params),
    queryFn: async () => handleApi(await getStrategiesStrategiesGet(params)),
  });
}

export function useInfiniteStrategiesQuery(
  params?: GetStrategiesStrategiesGetParams,
) {
  return useInfiniteQuery({
    queryKey: queryKeys.strategies(params),
    queryFn: async ({ pageParam = 1 }) =>
      handleApi(
        await getStrategiesStrategiesGet({ ...params, page: pageParam }),
      ),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.has_next) {
        return lastPage.page;
      }
      return undefined;
    },
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
