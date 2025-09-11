import BacktestBadge from "@/components/BacktestBadge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { Toaster } from "@/components/ui/sonner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { HTTP_BASE_URL } from "@/config";
import useFetch from "@/hooks/useFetch";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import type { DeploymentStatus } from "@/lib/types/deploymentStatus";
import type { TaskStatus } from "@/lib/types/taskStatus";
import {
  Ellipsis,
  MessageCircle,
  NotepadText,
  RotateCw,
  Trash2,
} from "lucide-react";
import React, { useState, type FC } from "react";
import { createPortal } from "react-dom";
import { useNavigate, useParams } from "react-router";
import { toast } from "sonner";

interface Position {
  id: string;
  instrument: string;
  side: string;
  order_type: string;
  starting_amount: number;
  current_amount: number | null;
  price: number | null;
  limit_price: number | null;
  stop_price: number | null;
  tp_price: number | null;
  sl_price: number | null;
  realised_pnl: number | null;
  unrealised_pnl: number | null;
  status: string;
  created_at: string;
  close_price: number | null;
  closed_at: string | null;
}

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

interface BacktestResult {
  status: TaskStatus;
  total_pnl: number | null;
  starting_balance: number | null;
  end_balance: number | null;
  total_trades: number | null;
  win_rate: number | null;
  created_at: string;
}

const BacktestsTable: FC<{ versionId: string }> = ({ versionId }) => {
  const [counter, setCounter] = useState<number>(0);

  const {
    data: backtests,
    loading,
    error,
  } = useFetch<BacktestResult[]>(
    HTTP_BASE_URL +
      `/strategies/versions/${versionId}/backtests?refresh=${counter}`,
    { credentials: "include" }
  );

  const [showCard, setShowCard] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const fd = new FormData(e.currentTarget);

    const rsp = await fetch(
      HTTP_BASE_URL + `/strategies/versions/${versionId}/backtest`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(fd),
      }
    );

    if (rsp.ok) {
      toast("Backtest initiated");
      setCounter((prev) => prev + 1);
    } else {
      const data = await rsp.json();
      toast(`Error: ${data.error}`);
    }

    setShowCard(false);
  };

  return (
    <>
      {showCard &&
        typeof document !== "undefined" &&
        createPortal(
          <Card className="z-50 fixed inset-0 flex items-center justify-center bg-black/30">
            <div className="bg-white p-6 rounded-md shadow-lg w-full max-w-md">
              <h2 className="text-lg font-bold mb-4">Launch Backtest</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Instrument
                  </label>
                  <input
                    type="text"
                    name="instrument"
                    placeholder="e.g. BTC/USDT"
                    className="w-full border rounded-md px-3 py-2"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Starting Balance
                  </label>
                  <input
                    type="number"
                    name="starting_balance"
                    placeholder="1000"
                    className="w-full border rounded-md px-3 py-2"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Leverage
                  </label>
                  <input
                    type="number"
                    name="leverage"
                    placeholder="10"
                    className="w-full border rounded-md px-3 py-2"
                    required
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowCard(false)}
                    className="px-4 py-2 rounded-md border border-gray-300 text-sm cursor-pointer"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="px-4 py-2 text-white rounded-md cursor-pointer"
                  >
                    Submit
                  </Button>
                </div>
              </form>
            </div>
          </Card>,
          document.body
        )}

      <div className="w-full h-7 relative mb-3">
        <div className="h-full absolute right-0 flex gap-3">
          <Button
            variant="outline"
            onClick={() => setCounter((prev) => prev + 1)}
            className="h-full"
          >
            <RotateCw />
          </Button>
          <Button onClick={() => setShowCard(true)} className="h-full">
            Launch
          </Button>
        </div>
      </div>

      <Table className="w-full h-full">
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
                    <div className="w-full h-full flex items-center justify-center">
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
                <Skeleton className="w-full h-full bg-gray-400" />
              </TableCell>
            </TableRow>
          )}

          {error && (
            <TableRow>
              <TableCell colSpan={7} className="h-50">
                <div className="w-full h-full flex items-center justify-center">
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

interface StrategyVersionResponse {
  version_id: string;
  strategy_id: string;
  name: string;
  prompt: string;
  backtest_status: TaskStatus;
  deployment_status: DeploymentStatus;
  created_at: string; // ISO string
}

const TABS = ["Backtests", "Deployments", "Positions"] as const;
type Tab = (typeof TABS)[number];

const DEFAULT_TAB = TABS[0];

const StrategyVersion: FC = () => {
  const { versionId } = useParams();
  const navigate = useNavigate();
  const { data, loading } = useFetch<StrategyVersionResponse>(
    HTTP_BASE_URL + `/strategies/versions/${versionId}`,
    { credentials: "include" }
  );

  const [tab, setTab] = useState<Tab>(DEFAULT_TAB);
  const [showPrompt, setShowPrompt] = useState<boolean>(false);

  const deleteVersion = async () => {
    if (!data) return;

    const rsp = await fetch(
      HTTP_BASE_URL + `/strategies/versions/${versionId}`,
      {
        method: "DELETE",
        credentials: "include",
      }
    );

    if (rsp.status === 200) {
      toast("Successfully deleted version.");
      setTimeout(() => {
        navigate(`/strategies/${data.strategy_id}`);
      }, 2000);
    } else {
      const d = await rsp.json();
      toast(`Error: ${d["error"]}`);
    }
  };

  return (
    <DashboardLayout className="mt-7">
      <Toaster />
      {showPrompt &&
        data &&
        typeof document !== "undefined" &&
        createPortal(
          <div className="z-[999] fixed inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm">
            <Card className="relative w-full max-w-2xl min-h-[300px] max-h-[600px] p-6 shadow-xl border border-gray-200">
              <h2 className="text-xl font-semibold mb-4">Prompt</h2>
              <div className="prose prose-sm w-full h-full text-gray-700 whitespace-pre-wrap min-h-[300px] overflow-y-scroll">
                {data.prompt}
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowPrompt(false)}
                className="absolute top-3 right-3 cursor-pointer"
              >
                Close
              </Button>
            </Card>
          </div>,
          document.body
        )}

      <div className="w-full sticky top-7 border-b-1 border-b-gray-200 mb-3">
        <div className="max-w-7xl mx-auto">
          <div className="w-full h-7 mb-3">
            {!loading && data ? (
              <div className="w-full h-full flex justify-between">
                <h1 className="text-2xl font-semibold">{data.name}</h1>
                <Popover
                  onOpenChange={(open) => {
                    if (!open) {
                      setShowPrompt(false);
                    }
                  }}
                >
                  <PopoverTrigger asChild>
                    <Button
                      variant="secondary"
                      className="!bg-transparent shadow-none cursor-pointer"
                    >
                      <Ellipsis />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent
                    className="z-50 w-30 flex flex-col gap-1 p-1"
                    side="bottom"
                    align="end"
                    forceMount
                  >
                    <Button
                      variant="secondary"
                      onClick={() => setShowPrompt(true)}
                      className="w-full h-7 flex flex-row items-center justify-start p-0 gap-1 bg-transparent shadow-none hover:bg-stone-100 cursor-pointer"
                    >
                      <NotepadText className="w-3 h-3" />
                      <span className="p-0 !bg-transparent text-xs">
                        Prompt
                      </span>
                    </Button>
                    <Button
                      variant="secondary"
                      className="w-full h-7 flex flex-row items-center justify-start gap-1 p-2 shadow-none bg-transparent  hover:bg-stone-100 cursor-pointer"
                    >
                      <MessageCircle className="w-3 h-3" />
                      <span className="p-0 !bg-transparent text-xs">Chat</span>
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => {
                        deleteVersion();
                      }}
                      className="w-full h-7 flex flex-row items-center justify-start gap-1 p-2 shadow-none bg-red-100 hover:bg-red-200 cursor-pointer"
                    >
                      <Trash2 className="w-3 h-3 text-red-500" />
                      <span className="p-0 !bg-transparent text-xs text-red-500">
                        Delete
                      </span>
                    </Button>
                  </PopoverContent>
                </Popover>
              </div>
            ) : (
              <Skeleton className="w-1/3 h-full rounded-lg bg-gray-300" />
            )}
          </div>
          <div className="w-full h-fit flex flex-row justify-start gap-1">
            {TABS.map((t) => (
              <Button
                key={t}
                variant="secondary"
                onClick={() => setTab(t)}
                className={`!bg-transparent shadow-none cursor-pointer rounded-none border-b-2 ${
                  tab == t
                    ? "border-b-gray-900"
                    : "border-b-transparent hover:border-b-gray-300"
                }`}
              >
                {t}
              </Button>
            ))}
          </div>
        </div>
      </div>
      <div className="w-full h-fit max-w-7xl mx-auto mb-3">
        {tab === "Backtests" && <BacktestsTable versionId={versionId!} />}
        {tab === "Positions" && <PositionsTable versionId={versionId!} />}
      </div>
    </DashboardLayout>
  );
};
export default StrategyVersion;
