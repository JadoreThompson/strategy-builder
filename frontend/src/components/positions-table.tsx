import useIntersectionObserver from "@/hooks/intersection-observer";
import { useInfinitePositionsQuery } from "@/hooks/strategy-version-hooks";
import type { PositionResponse } from "@/openapi";

import { useWsTokenQuery } from "@/hooks/auth-hooks";
import { usePositionWebsocketStore } from "@/stores/position-websocket-store";
import dayjs from "dayjs";
import { useEffect, useState, type FC } from "react";
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
  const [positions, setPositions] = useState<PositionResponse[]>([]);

  const wsConnect = usePositionWebsocketStore((state) => state.connect);
  const wsDisconnect = usePositionWebsocketStore((state) => state.disconnect);
  const eventsIterator = usePositionWebsocketStore(
    (state) => state.eventsIterator,
  );

  const wsTokenQuery = useWsTokenQuery();
  const infinitePositionsQuery = useInfinitePositionsQuery(versionId);
  const footerIntersectionObserver = useIntersectionObserver<HTMLDivElement>(
    () => {
      const pages = infinitePositionsQuery.data?.pages || [];
      if (pages.length && pages[0].has_next) {
        infinitePositionsQuery.fetchNextPage();
      }
    },
  );

  useEffect(() => {
    if (wsTokenQuery.error) {
      console.error(wsTokenQuery.error);
      return;
    }

    if (!wsTokenQuery.data) return;

    wsConnect(versionId, wsTokenQuery.data.token as string);

    const updatePositions = async () => {
      for await (const event of eventsIterator()) {
        const targetPos = event.position;

        if (event.type === "new")
          return setPositions((prev) => [targetPos, ...prev]);
        if (event.type === "update")
          return setPositions((prev) =>
            prev.map((pos) =>
              pos.position_id === targetPos.position_id ? targetPos : pos,
            ),
          );

        return positions;
      }
    };

    updatePositions();

    return () => {
      wsDisconnect();
    };
  }, []);

  useEffect(() => {
    const pages = infinitePositionsQuery.data?.pages;
    if (pages) {
      setPositions((prev) => [...prev, ...pages[pages.length - 1].data]);
    }
  }, [infinitePositionsQuery.data]);

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
              {positions.length ? (
                // infinitePositionsQuery.data.pages.map((page) =>
                //   page.data.map((p) => (
                //     <TableRow key={p.position_id}>
                //       <TableCell>{p.instrument}</TableCell>
                //       <TableCell>{p.side}</TableCell>
                //       <TableCell>{p.order_type}</TableCell>
                //       <TableCell>{p.starting_amount.toFixed(2)}</TableCell>
                //       <TableCell>
                //         {p.current_amount?.toFixed(2) ?? "-"}
                //       </TableCell>
                //       <TableCell>{p.price?.toFixed(2) ?? "-"}</TableCell>
                //       <TableCell>{p.realised_pnl?.toFixed(2) ?? "-"}</TableCell>
                //       <TableCell>
                //         {p.unrealised_pnl?.toFixed(2) ?? "-"}
                //       </TableCell>
                //       <TableCell>{p.status}</TableCell>
                //       <TableCell className="text-right">
                //         {dayjs(p.created_at).format("YYYY-MM-DD")}
                //       </TableCell>
                //     </TableRow>
                //   )),
                // )
                positions.map((p) => (
                  <TableRow key={p.position_id}>
                    <TableCell>{p.instrument}</TableCell>
                    <TableCell>{p.side}</TableCell>
                    <TableCell>{p.order_type}</TableCell>
                    <TableCell>{p.starting_amount}</TableCell>
                    <TableCell>{p.current_amount ?? "-"}</TableCell>
                    <TableCell>{p.price ?? "-"}</TableCell>
                    <TableCell>{p.realised_pnl ?? "-"}</TableCell>
                    <TableCell>{p.unrealised_pnl ?? "-"}</TableCell>
                    <TableCell>{p.status}</TableCell>
                    <TableCell className="text-right">
                      {dayjs(p.created_at).format("YYYY-MM-DD")}
                    </TableCell>
                  </TableRow>
                ))
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

          {infinitePositionsQuery.isPending && (
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
