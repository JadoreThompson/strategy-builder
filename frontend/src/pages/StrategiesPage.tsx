import { Input } from "@/components/ui/input";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { TaskStatus } from "@/lib/types/taskStatus";
import { Search } from "lucide-react";
import type { FC } from "react";
import { Link } from "react-router";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";

interface StrategyChartProps {
  dates: string[];
  pnls: number[];
}

export const StrategyChart: FC<{ data: { date: string; pnl: number }[] }> = ({
  data,
}) => {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        {/* <CartesianGrid strokeDasharray="3 3" /> */}
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
        {/* <YAxis dataKey="pnl" tick={{ fontSize: 12 }} /> */}
        <Tooltip />
        <Area
          type="monotone"
          dataKey="pnl"
          stroke="#5a76b9"
          fill="url(#fillMobile)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

interface StrategyPerformance {
  total_pnl: number;
  max_drawdown: number;
  win_rate: number;
  sharpe_ratio: number;
}

interface StrategyCardProps {
  strategy_id: string;
  name: string;
  backtestStatus: TaskStatus;
  stats: StrategyPerformance;
}

const StrategyCard: FC<StrategyCardProps> = ({
  strategy_id,
  name,
  backtestStatus,
  stats,
}) => {
  const getBacktestIconColor = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.NOT_STARTED:
        return "grey";
      case TaskStatus.PENDING:
        return "bg-orange-200/50 text-orange-500";
      case TaskStatus.COMPLETED:
        return "green";
      case TaskStatus.FAILED:
        return "red";
      default:
        return "grey";
    }
  };

  return (
    <Link
      to={`/strategies/${strategy_id}`}
      className="w-full h-full grid grid-cols-2 gap-2 p-3 border-1 border-gray-200 hover:shadow-md hover:shadow-gray-100 cursor-pointer"
    >
      <div className="flex flex-col gap-7">
        <div className="flex items-center gap-3">
          <h4 className="text-lg font-medium">{name}</h4>
          <span
            className={`text-xs w-fit h-fit p-1 ${getBacktestIconColor(
              backtestStatus
            )}`}
          >
            {(() => {
              const s = backtestStatus.toString();
              return s.charAt(0).toUpperCase() + s.slice(1);
            })()}
          </span>
        </div>
        <div className="flex flex-col gap-3">
          <div className="flex flex-row justify-between gap-2">
            <div className="flex justify-between w-1/2">
              <span className="text-sm">Pnl</span>
              <span className="text-md font-semibold">{stats.total_pnl}</span>
            </div>
            <div className="flex justify-between w-1/2">
              <span className="text-sm">Win Rate</span>
              <span className="text-md font-semibold">{stats.win_rate}</span>
            </div>
          </div>
          <div className="flex flex-row justify-between gap-2">
            <div className="flex justify-between w-1/2">
              <span className="text-sm">Max Drawdown</span>
              <span className="text-md font-semibold">
                {stats.max_drawdown}
              </span>
            </div>
            <div className="flex justify-between w-1/2">
              <span className="text-sm">Sharpe Ratio</span>
              <span className="text-md font-semibold">
                {stats.sharpe_ratio}
              </span>
            </div>
          </div>
        </div>
      </div>
      {/* Stats Chart */}
      <div className="h-full">
        <StrategyChart
          data={[
            { date: "2024-01-01", pnl: 100 },
            { date: "2024-01-02", pnl: 200 },
            { date: "2024-01-03", pnl: 150 },
            { date: "2024-01-04", pnl: 300 },
            { date: "2024-01-05", pnl: 250 },
            { date: "2024-01-06", pnl: 400 },
          ]}
        />
      </div>
    </Link>
  );
};

const StrategiesPage: FC = () => {
  return (
    <DashboardLayout>
      <h1 className="text-2xl font-semibold">Strategies</h1>
      <div className="w-full flex justify-end mb-3">
        <div className="flex items-center border-1 border-gray-200 px-2">
          <Search className="text-gray-600 w-5 h-5" />
          <Input placeholder="Search" className="border-none focus:!ring-0" />
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <div className="w-full h-50">
          <StrategyCard
            strategy_id={"1"}
            name="optimus"
            backtestStatus={TaskStatus.PENDING}
            stats={{
              max_drawdown: 50.0,
              win_rate: 50,
              sharpe_ratio: 6.7,
              total_pnl: 2000,
            }}
          />
        </div>
      </div>
    </DashboardLayout>
  );
};
export default StrategiesPage;
