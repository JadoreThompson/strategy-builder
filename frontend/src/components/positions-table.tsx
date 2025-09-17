import { HTTP_BASE_URL } from "@/config";
import useFetch from "@/hooks/useFetch";
import type { Position } from "@/lib/types/position";

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
  const {
    data: positions,
    loading,
    error,
  } = useFetch<Position[]>(
    HTTP_BASE_URL + `/strategies/versions/${versionId}/positions`,
    {
      credentials: "include",
    }
  );

  return (
    <Table className="w-full h-full">
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
        {!loading && !error && (
          <>
            {positions!.length > 0 ? (
              positions!.map((p, idx) => (
                <TableRow key={idx}>
                  <TableCell>{p.instrument}</TableCell>
                  <TableCell>{p.side}</TableCell>
                  <TableCell>{p.order_type}</TableCell>
                  <TableCell>{p.starting_amount.toFixed(2)}</TableCell>
                  <TableCell>{p.current_amount?.toFixed(2) ?? "-"}</TableCell>
                  <TableCell>{p.price?.toFixed(2) ?? "-"}</TableCell>
                  <TableCell>{p.realised_pnl?.toFixed(2) ?? "-"}</TableCell>
                  <TableCell>{p.unrealised_pnl?.toFixed(2) ?? "-"}</TableCell>
                  <TableCell>{p.status}</TableCell>
                  <TableCell className="text-right">
                    {new Date(p.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={10} className="h-50 !bg-gray-100">
                  <div className="w-full h-full flex items-center justify-center">
                    <span>No positions</span>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </>
        )}

        {loading && (
          <TableRow>
            <TableCell colSpan={10} className="h-50">
              <Skeleton className="w-full h-full bg-gray-100" />
            </TableCell>
          </TableRow>
        )}

        {error && (
          <TableRow>
            <TableCell colSpan={10} className="h-50">
              <div className="w-full h-full flex items-center justify-center">
                <span>{error.message}</span>
              </div>
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
};

export default PositionsTable;
