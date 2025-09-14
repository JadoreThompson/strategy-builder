import BacktestBadge from "@/components/BacktestBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { HTTP_BASE_URL } from "@/config";
import useFetch from "@/hooks/useFetch";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { type TaskStatus } from "@/lib/types/taskStatus";
import { Search } from "lucide-react";
import { useEffect, useState, type FC } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";

interface BacktestChartProps {
  versionId: string;
}

interface ChartDataPoint {
  date: string;
  pnl: number;
}

const BacktestChart: FC<BacktestChartProps> = ({ versionId }) => {
  const [data, setData] = useState<ChartDataPoint[] | null>(null);
  const { data: backtests } = useFetch<
    { backtest_id: string; created_at: string }[]
  >(`${HTTP_BASE_URL}/strategies/versions/${versionId}/backtests`, {
    credentials: "include",
  });

  useEffect(() => {
    if (!backtests || !backtests.length) return;

    const latestBacktest = backtests[backtests.length - 1];

    if (!latestBacktest) return;

    fetch(
      `${HTTP_BASE_URL}/backtests/${latestBacktest.backtest_id}/positions-chart`,
      { credentials: "include" }
    )
      .then((res) => res.json())
      .then((chartData: ChartDataPoint[]) => setData(chartData))
      .catch(console.error);
  }, [backtests]);

  if (!data)
    return (
      <div className="h-full flex items-center justify-center">
        Loading chart...
      </div>
    );

  if (!data.length) {
    return (
      <div className="h-full flex items-center justify-center">
        No backtests
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
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

interface StrategyVersionPerformance {
  total_pnl: number | null;
  max_drawdown: number | null;
  win_rate: number | null;
  sharpe_ratio: number | null;
}

interface StrategyVersionCardProps {
  version_id: string;
  name: string;
  backtestStatus?: TaskStatus;
  stats: StrategyVersionPerformance;
}

const StrategyVersionCard: FC<StrategyVersionCardProps> = ({
  version_id,
  name,
  backtestStatus,
  stats,
}) => {
  return ( 
    <Link
      to={`/strategies/versions/${version_id}`}
      className="w-full h-full grid grid-cols-2 gap-2 p-3 border-1 border-gray-200 hover:shadow-md hover:shadow-gray-100 cursor-pointer"
    >
      <div className="flex flex-col gap-7 py-3">
        <div className="flex items-center gap-3">
          <h4 className="text-lg font-medium">{name}</h4>
          {backtestStatus && (
            <BacktestBadge
              status={backtestStatus}
              className="text-xs w-fit h-fit p-1"
            />
          )}
        </div>
        <div className="flex flex-col gap-3">
          <div className="flex flex-row justify-between gap-2">
            <div className="flex justify-between w-1/2">
              <span className="text-sm">Pnl</span>
              <span className="text-md font-semibold">
                {typeof stats.total_pnl === "number" ? stats.total_pnl : "-"}
              </span>
            </div>
            <div className="flex justify-between w-1/2">
              <span className="text-sm">Win Rate</span>
              <span className="text-md font-semibold">
                {typeof stats.win_rate === "number" ? stats.win_rate : "-"}
              </span>
            </div>
          </div>
          <div className="flex flex-row justify-between gap-2">
            <div className="flex justify-between w-1/2">
              <span className="text-sm">Max Drawdown</span>
              <span className="text-md font-semibold">
                {typeof stats.max_drawdown === "number"
                  ? stats.max_drawdown
                  : "-"}
              </span>
            </div>
            <div className="flex justify-between w-1/2">
              <span className="text-sm">Sharpe Ratio</span>
              <span className="text-md font-semibold">
                {typeof stats.sharpe_ratio === "number"
                  ? stats.sharpe_ratio
                  : "-"}
              </span>
            </div>
          </div>
        </div>
      </div>
      {/* Stats Chart */}
      <div className="h-full">
        <BacktestChart versionId={version_id} />
      </div>
    </Link>
  );
};

interface BacktestResults {
  status: TaskStatus;
  total_pnl: number | null;
  starting_balance: number | null;
  end_balance: number | null;
  total_trades: number | null;
  win_rate: number | null;
  created_at: string; // ISO datetime string
}

interface StrategyVersionsResponse {
  version_id: string; // UUID as string
  name: string;
  created_at: string; // ISO datetime string
  backtest: BacktestResults | null;
}

const StrategiesVersionsPage: FC = () => {
  const { strategyId } = useParams();
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState("");

  const { data } = useFetch<StrategyVersionsResponse[]>(
    HTTP_BASE_URL +
      `/strategies/${strategyId}/versions` +
      (searchText ? `?name=${encodeURIComponent(searchText)}` : ""),
    { credentials: "include" }
  );

  return (
    <DashboardLayout>
      <h1 className="text-2xl font-semibold mb-3">Versions</h1>
      <div className="w-full h-7 flex justify-between mb-3">
        <Button
          onClick={() => navigate(`/create-version?strategy_id=${strategyId}`)}
          className="h-full"
        >
          Create
        </Button>
        <div className="h-full flex items-center border-1 border-gray-200 px-2">
          <Search className="text-gray-600 w-5 h-5" />
          <Input
            placeholder="Search"
            className="border-none focus:!ring-0"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {(data ?? []).length ? (
          data!.map((version) => (
            <div key={version.version_id} className="w-full h-50">
              <StrategyVersionCard
                version_id={version.version_id}
                name={version.name}
                backtestStatus={version.backtest?.status}
                stats={
                  version.backtest
                    ? {
                        max_drawdown: 50.0,
                        win_rate: version.backtest.win_rate,
                        sharpe_ratio: 6.7,
                        total_pnl: version.backtest.total_pnl,
                      }
                    : ({} as StrategyVersionPerformance)
                }
              />
            </div>
          ))
        ) : (
          <p className="text-center text-gray-500">No versions found</p>
        )}
      </div>
    </DashboardLayout>
  );
};

export default StrategiesVersionsPage;
