import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  getBacktestPositionsChartBacktestsBacktestIdPositionsChartGet,
  getBacktestResultBacktestsBacktestIdGet,
} from "@/openapi";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";

export function useBacktestResultQuery(backtestId: string) {
  return useQuery({
    queryKey: queryKeys.backtestResult(backtestId),
    queryFn: async () =>
      handleApi(await getBacktestResultBacktestsBacktestIdGet(backtestId)),
    enabled: !!backtestId,
  });
}

export function useBacktestPositionsChartQuery(backtestId: string) {
  return useQuery({
    queryKey: queryKeys.backtestPositionsChart(backtestId),
    queryFn: async () =>
      handleApi(
        await getBacktestPositionsChartBacktestsBacktestIdPositionsChartGet(
          backtestId,
        ),
      ),
    enabled: !!backtestId,
  });
}
