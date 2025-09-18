import { useBacktestsQuery } from "@/hooks/strategy-version-hooks";
import { useEffect, type FC } from "react";
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

const BacktestsTable: FC<{ versionId: string; refreshCounter: number }> = (
  props,
) => {
  const backtestsQuery = useBacktestsQuery(props.versionId);
  useEffect(() => {
    backtestsQuery.refetch();
  }, [props.refreshCounter]);

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
          {backtestsQuery.isPending && (
            <TableRow>
              <TableCell colSpan={7} className="h-50">
                <Skeleton className="h-full w-full bg-gray-100" />
              </TableCell>
            </TableRow>
          )}

          {backtestsQuery.data && (
            <>
              {backtestsQuery.data.length > 0 ? (
                <>
                  {backtestsQuery.data.map((b, idx) => (
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

          {backtestsQuery.error && (
            <TableRow>
              <TableCell colSpan={7} className="h-50">
                <div className="flex h-full w-full items-center justify-center">
                  <span>{backtestsQuery.error.message}</span>
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
