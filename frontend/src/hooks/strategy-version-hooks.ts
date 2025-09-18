import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  createBacktestStrategiesVersionsVersionIdBacktestPost,
  deleteVersionStrategiesVersionsVersionIdDelete,
  getBacktestsStrategiesVersionsVersionIdBacktestsGet,
  getPositionsStrategiesVersionsVersionIdPositionsGet,
  getStrategyVersionStrategiesVersionsVersionIdGet,
  getStrategyVersionsStrategiesStrategyIdVersionsGet,
  type BacktestCreate,
  type GetStrategyVersionsStrategiesStrategyIdVersionsGetParams,
} from "@/openapi";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useStrategyVersionsQuery(
  params: {
    strategyId: string;
  } & GetStrategyVersionsStrategiesStrategyIdVersionsGetParams,
) {
  return useQuery({
    queryKey: queryKeys.strategyVersions(params),
    queryFn: async () =>
      handleApi(
        await getStrategyVersionsStrategiesStrategyIdVersionsGet(
          params.strategyId,
          params,
        ),
      ),
    enabled: !!params.strategyId,
  });
}

export function useStrategyVersionQuery(versionId: string) {
  return useQuery({
    queryKey: queryKeys.strategyVersion(versionId),
    queryFn: async () =>
      handleApi(
        await getStrategyVersionStrategiesVersionsVersionIdGet(versionId),
      ),
    enabled: !!versionId,
  });
}

export function useDeleteStrategyVersionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { versionId: string; strategyId: string }) =>
      handleApi(
        await deleteVersionStrategiesVersionsVersionIdDelete(params.versionId),
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.strategyVersions({
          strategyId: variables.strategyId,
        }),
      });
    },
  });
}

export function useCreateBacktestMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { versionId: string; data: BacktestCreate }) =>
      handleApi(
        await createBacktestStrategiesVersionsVersionIdBacktestPost(
          params.versionId,
          params.data,
        ),
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.strategyVersionBacktests(variables.versionId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.strategyVersion(variables.versionId),
      });
    },
  });
}

export function useBacktestsQuery(versionId: string) {
  return useQuery({
    queryKey: queryKeys.strategyVersionBacktests(versionId),
    queryFn: async () =>
      handleApi(
        await getBacktestsStrategiesVersionsVersionIdBacktestsGet(versionId),
      ),
    enabled: !!versionId,
  });
}

export function usePositionsQuery(versionId: string) {
  return useQuery({
    queryKey: queryKeys.strategyVersionPositions(versionId),
    queryFn: async () =>
      handleApi(
        await getPositionsStrategiesVersionsVersionIdPositionsGet(versionId),
      ),
    enabled: !!versionId,
  });
}
