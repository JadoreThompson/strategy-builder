import BacktestBadge from "@/components/backtest-badge";
import ScrollTop from "@/components/scroll-top";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import useIntersectionObserver from "@/hooks/intersection-observer";
import {
  useBacktestsQuery,
  useInfiniteStrategyVersionsQuery,
} from "@/hooks/strategy-version-hooks";
import { DashboardLayout } from "@/layouts/dashboard-layout";
import { queryClient } from "@/lib/query/query-client";
import type { StrategyVersionsResponse } from "@/openapi";
import { Search } from "lucide-react";
import { useEffect, useRef, useState, type FC } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";

const BacktestChart: FC<{
  versionId: string;
}> = ({ versionId }) => {
  const backtestsQuery = useBacktestsQuery(versionId);

  if (backtestsQuery.isPending)
    return (
      <div className="flex h-full items-center justify-center">
        Loading chart...
      </div>
    );

  if (backtestsQuery.error)
    return (
      <div className="flex h-full items-center justify-center">
        Error loading chart...
      </div>
    );

  if (!backtestsQuery.data.size) {
    return (
      <div className="flex h-full items-center justify-center">
        No backtests
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={backtestsQuery.data.data}>
        <defs>
          <linearGradient id="fillMobile" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#8297ca" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#dee4f1" stopOpacity={0.1} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          formatter={(value, name, props) => {
            if (name === "balance") {
              const pnl = props.payload?.pnl;

              return [
                `$${value.toFixed(2)}`,
                `Balance (PnL: $${pnl?.toFixed(2)})`,
              ];
            }
            return [value, name];
          }}
        />
        <Area
          type="monotone"
          dataKey="balance"
          stroke="#5a76b9"
          fill="url(#fillMobile)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

const StrategyVersionCard: FC<StrategyVersionsResponse> = (props) => {
  return (
    <Link
      to={`/strategies/versions/${props.version_id}`}
      className="grid h-full w-full cursor-pointer grid-cols-2 gap-2 border-1 border-gray-200 p-3 hover:shadow-md hover:shadow-gray-100"
    >
      <div className="flex flex-col gap-7 py-3">
        <div className="flex items-center gap-3">
          <h4 className="text-lg font-medium">{props.name}</h4>
          {props.backtest?.status && (
            <BacktestBadge
              status={props.backtest.status}
              className="h-fit w-fit p-1 text-xs"
            />
          )}
        </div>
        <div className="flex flex-col gap-3">
          <div className="flex flex-row justify-between gap-2">
            <div className="flex w-1/2 justify-between">
              <span className="text-sm">Pnl</span>
              <span className="text-md font-semibold">
                {typeof props.backtest?.total_pnl === "number"
                  ? props.backtest.total_pnl
                  : "-"}
              </span>
            </div>
            <div className="flex w-1/2 justify-between">
              <span className="text-sm">Win Rate</span>
              <span className="text-md font-semibold">
                {typeof props.backtest?.win_rate === "number"
                  ? props.backtest.win_rate
                  : "-"}
              </span>
            </div>
          </div>
          <div className="flex flex-row justify-between gap-2">
            <div className="flex w-1/2 justify-between">
              <span className="text-sm">Max Drawdown</span>
              <span className="text-md font-semibold">-</span>
            </div>
            <div className="flex w-1/2 justify-between">
              <span className="text-sm">Sharpe Ratio</span>
              <span className="text-md font-semibold">-</span>
            </div>
          </div>
        </div>
      </div>
      {/* Stats Chart */}
      <div className="h-full">
        <BacktestChart versionId={props.version_id} />
      </div>
    </Link>
  );
};

const StrategiesVersionsPage: FC = () => {
  const { strategyId } = useParams<{ strategyId: string }>();
  const navigate = useNavigate();

  const [searchText, setSearchText] = useState("");

  const prevSearchTextRef = useRef<string>(searchText);
  const infiniteVersionsQuery = useInfiniteStrategyVersionsQuery({
    strategyId: strategyId!,
    name: searchText,
  });
  const listFooterIntersectionObserver =
    useIntersectionObserver<HTMLDivElement>(() => {
      const pages = infiniteVersionsQuery.data?.pages || [];
      if (!pages.length || pages[pages.length - 1].has_next) {
        infiniteVersionsQuery.fetchNextPage();
      }
    });

  useEffect(() => {
    if (prevSearchTextRef.current !== searchText) {
      prevSearchTextRef.current = searchText;
      queryClient.clear();

      if (infiniteVersionsQuery.isPending) {
        infiniteVersionsQuery.fetchNextPage();
      }
    }
  }, [searchText]);

  const versionExist =
    infiniteVersionsQuery.data?.pages &&
    infiniteVersionsQuery.data.pages[0].size;

  return (
    <DashboardLayout>
      <ScrollTop />

      <h1 className="mb-3 text-2xl font-semibold">Versions</h1>
      <div className="mb-3 flex h-9 w-full justify-between">
        <Button
          onClick={() => navigate(`/create-version?strategy_id=${strategyId}`)}
          className="h-full"
        >
          Create
        </Button>
        <div className="flex h-full items-center border-1 border-gray-200 px-2">
          <Search className="h-5 w-5 text-gray-600" />
          <Input
            placeholder="Search"
            className="h-full border-none focus:!ring-0"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </div>
      </div>

      <div className="flex h-5000 flex-col gap-2">
        {versionExist ? (
          infiniteVersionsQuery.data?.pages.map((page) =>
            page.data.map((version) => (
              <>
                <div key={version.version_id} className="h-50 w-full">
                  <StrategyVersionCard {...version} />
                </div>
              </>
            )),
          )
        ) : (
          <div className="flex h-40 w-full items-center justify-center text-gray-500">
            {infiniteVersionsQuery.isPending ? (
              <>
                Loading
                <p className="ellipsis"></p>
              </>
            ) : (
              <>
                {searchText
                  ? "No versions found matching your search."
                  : "No versions found for this strategy."}
              </>
            )}
          </div>
        )}
        <div ref={listFooterIntersectionObserver.refObj}></div>
        {infiniteVersionsQuery.isFetching &&
          infiniteVersionsQuery.data?.pages.length && (
            <div className="mt-4 flex h-8 w-full items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-stone-300 border-t-transparent"></div>
            </div>
          )}
      </div>
    </DashboardLayout>
  );
};

export default StrategiesVersionsPage;
