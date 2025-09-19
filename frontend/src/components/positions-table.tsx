import useIntersectionObserver from "@/hooks/intersection-observer";
import {
  useInfinitePositionsQuery,
  usePositionsQuery,
} from "@/hooks/strategy-version-hooks";
import dayjs from "dayjs";
import type { FC } from "react";
import { Skeleton } from "./ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

const PositionsTable: FC<{ versionId: string }> = ({ versionId }) => {
  const positionsQuery = usePositionsQuery(versionId);

  const infinitePositionsQuery = useInfinitePositionsQuery(versionId);
  const footerIntersectionObserver = useIntersectionObserver<HTMLDivElement>(
    () => {
      const pages = infinitePositionsQuery.data?.pages || [];
      if (pages.length && pages[0].has_next) {
        infinitePositionsQuery.fetchNextPage();
      }
    },
  );

  const foundPositions =
    infinitePositionsQuery.data &&
    infinitePositionsQuery.data.pages.length &&
    infinitePositionsQuery.data.pages[0].size;

  return (
    <>
      <Table className="h-full w-full">
        <TableHeader>
          <TableRow>
            <TableHead>Instrument</TableHead>
            <TableHead>Side</TableHead>
            <TableHead>Order Type</TableHead>
            <TableHead>Starting Amount</TableHead>
            <TableHead>Current Amount</TableHead>
            <TableHead>Price</TableHead>
            <TableHead>Realised PnL</TableHead>
            <TableHead>Unrealised PnL</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Created At</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {infinitePositionsQuery.error && (
            <TableRow>
              <TableCell colSpan={10} className="h-50">
                <div className="flex h-full w-full items-center justify-center">
                  <span>{infinitePositionsQuery.error.message}</span>
                </div>
              </TableCell>
            </TableRow>
          )}

          {infinitePositionsQuery.data && (
            <>
              {foundPositions ? (
                infinitePositionsQuery.data.pages.map((page) =>
                  page.data.map((p) => (
                    <TableRow key={p.position_id}>
                      <TableCell>{p.instrument}</TableCell>
                      <TableCell>{p.side}</TableCell>
                      <TableCell>{p.order_type}</TableCell>
                      <TableCell>{p.starting_amount.toFixed(2)}</TableCell>
                      <TableCell>
                        {p.current_amount?.toFixed(2) ?? "-"}
                      </TableCell>
                      <TableCell>{p.price?.toFixed(2) ?? "-"}</TableCell>
                      <TableCell>{p.realised_pnl?.toFixed(2) ?? "-"}</TableCell>
                      <TableCell>
                        {p.unrealised_pnl?.toFixed(2) ?? "-"}
                      </TableCell>
                      <TableCell>{p.status}</TableCell>
                      <TableCell className="text-right">
                        {dayjs(p.created_at).format("YYYY-MM-DD")}
                      </TableCell>
                    </TableRow>
                  )),
                )
              ) : (
                <TableRow>
                  <TableCell colSpan={10} className="h-50 !bg-gray-100">
                    <div className="flex h-full w-full items-center justify-center">
                      <span>No positions</span>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </>
          )}

          {positionsQuery.isPending && (
            <TableRow>
              <TableCell colSpan={10} className="h-50">
                <Skeleton className="h-full w-full bg-gray-100" />
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <div ref={footerIntersectionObserver.elementRefObj}></div>
    </>
  );
};

export default PositionsTable;
