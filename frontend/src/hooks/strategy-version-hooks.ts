import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  createBacktestStrategiesVersionsVersionIdBacktestPost,
  deleteVersionStrategiesVersionsVersionIdDelete,
  getBacktestsStrategiesVersionsVersionIdBacktestsGet,
  getDeploymentsStrategiesVersionIdDeploymentsGet,
  getPositionsStrategiesVersionsVersionIdPositionsGet,
  getStrategyVersionStrategiesVersionsVersionIdGet,
  getStrategyVersionsStrategiesStrategyIdVersionsGet,
  type BacktestCreate,
  type GetStrategyVersionsStrategiesStrategyIdVersionsGetParams,
} from "@/openapi";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

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

export function useInfiniteStrategyVersionsQuery(
  params: {
    strategyId: string;
  } & GetStrategyVersionsStrategiesStrategyIdVersionsGetParams,
) {
  return useInfiniteQuery({
    queryKey: queryKeys.strategyVersions(params),
    queryFn: async ({ pageParam = 1 }) =>
      handleApi(
        await getStrategyVersionsStrategiesStrategyIdVersionsGet(
          params.strategyId,
          { ...params, page: pageParam },
        ),
      ),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.has_next) {
        return lastPage.page + 1;
      }
      return undefined;
    },
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

export function useInfiniteBacktestsQuery(versionId: string) {
  return useInfiniteQuery({
    queryKey: ["strategy-version-backtests-query-key", versionId],
    queryFn: async ({ pageParam = 1 }) => {
      return handleApi(
        await getBacktestsStrategiesVersionsVersionIdBacktestsGet(versionId, {
          page: pageParam,
        }),
      );
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.has_next) {
        return lastPage.page + 1;
      }
      return undefined;
    },
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

export function useInfinitePositionsQuery(versionId: string) {
  return useInfiniteQuery({
    queryKey: ["strategy-version-positions-query-key", versionId],
    queryFn: async ({ pageParam = 1 }) => {
      return handleApi(
        await getPositionsStrategiesVersionsVersionIdPositionsGet(versionId, {
          page: pageParam,
        }),
      );
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.has_next) {
        return lastPage.page + 1;
      }
      return undefined;
    },
  });
}

export function useInfiniteDeploymentsQuery(versionId: string) {
  return useInfiniteQuery({
    queryKey: ["strategy-version-deployments-query-key", versionId],
    queryFn: async ({ pageParam = 1 }) => {
      return handleApi(
        await getDeploymentsStrategiesVersionIdDeploymentsGet(versionId, {
          page: pageParam,
        }),
      );
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.has_next) {
        return lastPage.page + 1;
      }
      return undefined;
    },
  });
}
