import useIntersectionObserver from "@/hooks/intersection-observer";
import { useInfiniteBacktestsQuery } from "@/hooks/strategy-version-hooks";
import React, { useEffect, type FC } from "react";
import BacktestBadge from "./backtest-badge";
import Spinner from "./spinner";
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
  const infiniteBacktestsQuery = useInfiniteBacktestsQuery(props.versionId);

  const tableFooterIntersectionObserver =
    useIntersectionObserver<HTMLDivElement>(() => {
      const pages = infiniteBacktestsQuery.data?.pages || [];
      if (!pages.length || pages[pages.length - 1].has_next) {
        infiniteBacktestsQuery.fetchNextPage();
      }
    });

  useEffect(() => {
    infiniteBacktestsQuery.refetch();
  }, [props.refreshCounter]);

  const backtestsFound =
    infiniteBacktestsQuery.data &&
    infiniteBacktestsQuery.data.pages.length &&
    infiniteBacktestsQuery.data.pages[0].size;

  return (
    <div>
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
          {infiniteBacktestsQuery.isPending && (
            <TableRow>
              <TableCell colSpan={7} className="h-50">
                <Skeleton className="h-full w-full bg-gray-100" />
              </TableCell>
            </TableRow>
          )}

          {infiniteBacktestsQuery.data?.pages.map((page, pageIdx) => (
            <React.Fragment key={pageIdx}>
              {page.data.map((b) => (
                <TableRow key={b.backtest_id}>
                  <TableCell>
                    <BacktestBadge status={b.status} className="p-1 text-xs" />
                  </TableCell>
                  <TableCell>{b.total_pnl?.toFixed(2) ?? "-"}</TableCell>
                  <TableCell>{b.starting_balance?.toFixed(2) ?? "-"}</TableCell>
                  <TableCell>{b.end_balance?.toFixed(2) ?? "-"}</TableCell>
                  <TableCell>{b.total_trades ?? "-"}</TableCell>
                  <TableCell>{b.win_rate?.toFixed(2) ?? "-"}</TableCell>
                  <TableCell className="text-right">
                    {new Date(b.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </React.Fragment>
          ))}

          {!infiniteBacktestsQuery.isPending && !backtestsFound && (
            <TableRow>
              <TableCell colSpan={7} className="h-50 !bg-gray-100">
                <div className="flex h-full w-full items-center justify-center">
                  <span>No backtests have been run for this version.</span>
                </div>
              </TableCell>
            </TableRow>
          )}

          {infiniteBacktestsQuery.error && (
            <TableRow>
              <TableCell colSpan={7} className="h-50">
                <div className="flex h-full w-full items-center justify-center">
                  <span>{infiniteBacktestsQuery.error.message}</span>
                </div>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      <div ref={tableFooterIntersectionObserver.elementRefObj} />
      {infiniteBacktestsQuery.isFetchingNextPage && <Spinner />}
    </div>
  );
};

export default BacktestsTable;
