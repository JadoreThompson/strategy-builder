import { HTTP_BASE_URL } from "@/config";
import useFetch from "@/hooks/useFetch";
import type { TaskStatus } from "@/lib/types/taskStatus";
import { type FC } from "react";
import BacktestBadge from "./backtest-badge";
import { Skeleton } from "./ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

interface BacktestResult {
  status: TaskStatus;
  total_pnl: number | null;
  starting_balance: number | null;
  end_balance: number | null;
  total_trades: number | null;
  win_rate: number | null;
  created_at: string;
}

const BacktestsTable: FC<{ versionId: string; refreshCounter: number }> = ({
  versionId,
  refreshCounter,
}) => {
  const {
    data: backtests,
    loading,
    error,
  } = useFetch<BacktestResult[]>(
    HTTP_BASE_URL +
      `/strategies/versions/${versionId}/backtests?refresh=${refreshCounter}`,
    { credentials: "include" },
  );

  return (
    <>
      <Table className="h-full w-full">
        <TableHeader>
          <TableRow>
            <TableHead>Status</TableHead>
            <TableHead>Total PnL</TableHead>
            <TableHead>Starting Balance</TableHead>
            <TableHead>End Balance</TableHead>
            <TableHead>Total Trades</TableHead>
            <TableHead>Win Rate</TableHead>
            <TableHead className="text-right">Created At</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {!loading && !error && (
            <>
              {backtests!.length > 0 ? (
                <>
                  {backtests!.map((b, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <BacktestBadge
                          status={b.status}
                          className="p-1 text-xs"
                        />
                      </TableCell>
                      <TableCell>{b.total_pnl?.toFixed(2) ?? "-"}</TableCell>
                      <TableCell>
                        {b.starting_balance?.toFixed(2) ?? "-"}
                      </TableCell>
                      <TableCell>{b.end_balance?.toFixed(2) ?? "-"}</TableCell>
                      <TableCell>{b.total_trades ?? "-"}</TableCell>
                      <TableCell>{b.win_rate?.toFixed(2) ?? "-"}</TableCell>
                      <TableCell className="text-right">
                        {new Date(b.created_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </>
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="h-50 !bg-gray-100">
                    <div className="flex h-full w-full items-center justify-center">
                      <span>No backtests</span>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </>
          )}

          {loading && (
            <TableRow>
              <TableCell colSpan={7} className="h-50">
                <Skeleton className="h-full w-full bg-gray-100" />
              </TableCell>
            </TableRow>
          )}

          {error && (
            <TableRow>
              <TableCell colSpan={7} className="h-50">
                <div className="flex h-full w-full items-center justify-center">
                  <span>{error.message}</span>
                </div>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </>
  );
};

export default BacktestsTable;
