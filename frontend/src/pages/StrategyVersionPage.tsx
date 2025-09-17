import BacktestsTable from "@/components/backtests-table";
import CreateBacktestCard from "@/components/create-backtest-card";
import CreateDeploymentCard from "@/components/create-deployment-card";
import DeploymentsTable from "@/components/deployments-table";
import PositionsTable from "@/components/positions-table";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { Toaster } from "@/components/ui/sonner";
import { HTTP_BASE_URL } from "@/config";
import useFetch from "@/hooks/useFetch";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import type { AccountResponse } from "@/lib/types/accountResponse";
import type { DeploymentStatus } from "@/lib/types/deploymentStatus";
import type { TaskStatus } from "@/lib/types/taskStatus";
import {
  Ellipsis,
  MessageCircle,
  NotepadText,
  Rocket,
  RotateCw,
  Trash2,
} from "lucide-react";
import { useState, type FC } from "react";
import { createPortal } from "react-dom";
import { useNavigate, useParams } from "react-router";
import { toast } from "sonner";

const BacktestActions: FC<{
  onRefresh: () => void;
  onNewBacktest: () => void;
}> = ({ onRefresh, onNewBacktest }) => {
  return (
    <div className="h-full flex gap-3">
      <Button
        variant="outline"
        onClick={onRefresh}
        className="h-full cursor-pointer"
        aria-label="Refresh backtests"
      >
        <RotateCw />
      </Button>
      <Button onClick={onNewBacktest} className="h-full cursor-pointer">
        Backtest
      </Button>
    </div>
  );
};

const DeploymentsActions: FC<{
  onRefresh: () => void;
  onNewDeployment: () => void;
}> = ({ onRefresh, onNewDeployment }) => {
  return (
    <div className="h-full flex gap-3">
      <Button
        variant="outline"
        onClick={onRefresh}
        className="h-full cursor-pointer"
        aria-label="Refresh backtests"
      >
        <RotateCw />
      </Button>
      <Button onClick={onNewDeployment} className="h-full cursor-pointer">
        Deploy
      </Button>
    </div>
  );
};

const CreateDeploymentCardWrapper: FC<{
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void | Promise<void>;
  onClose: () => void | Promise<void>;
}> = ({ onSubmit, onClose }) => {
  const { data: accounts, loading: accountsLoading } = useFetch<
    AccountResponse[]
  >(`${HTTP_BASE_URL}/accounts/`, { credentials: "include" });

  return (
    <CreateDeploymentCard
      accounts={accounts || []}
      loading={accountsLoading}
      onSubmit={onSubmit}
      onClose={onClose}
    />
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

const StrategyVersionPage: FC = () => {
  const { versionId } = useParams();
  const navigate = useNavigate();
  const { data, loading } = useFetch<StrategyVersionResponse>(
    HTTP_BASE_URL + `/strategies/versions/${versionId}`,
    { credentials: "include" }
  );

  const [tab, setTab] = useState<Tab>(DEFAULT_TAB);
  const [showPrompt, setShowPrompt] = useState<boolean>(false);

  const [backtestRefreshCounter, setBacktestRefreshCounter] =
    useState<number>(0);
  const [showCreateBacktestCard, setShowCreateBacktestCard] =
    useState<boolean>(false);
  const [deploymentRefreshCounter, setDeploymentRefreshCounter] =
    useState<number>(0);
  const [showCreateDeploymentCard, setShowCreateDeploymentCard] =
    useState<boolean>(false);

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

  const handleOnBacktestSubmit = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
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
        body: JSON.stringify(Object.fromEntries(fd.entries())),
      }
    );

    if (rsp.ok) {
      toast("Backtest initiated");
      setBacktestRefreshCounter((prev) => prev + 1);
    } else {
      const data = await rsp.json();
      toast(`Error: ${data.error}`);
    }
  };

  const handleOnDeploymentSubmit = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault();

    const fd = new FormData(e.currentTarget);
    const account_id = fd.get("account_id");
    const instrument = fd.get("instrument");

    if (!account_id) {
      toast("Error: Please select an account.");
      return;
    }

    const rsp = await fetch(`${HTTP_BASE_URL}/deployments/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({
        account_id,
        version_id: versionId,
        instrument,
      }),
    });

    if (rsp.ok) {
      toast("Deployment initiated successfully.");
      setDeploymentRefreshCounter((prev) => prev + 1);
    } else {
      const data = await rsp.json();
      toast(`Error: ${data.detail || "Failed to create deployment."}`);
    }

    setShowCreateDeploymentCard(false);
  };

  return (
    <DashboardLayout className="mt-7">
      <Toaster />

      {showCreateBacktestCard &&
        typeof document !== "undefined" &&
        createPortal(
          <CreateBacktestCard
            onSubmit={handleOnBacktestSubmit}
            onClose={() => setShowCreateBacktestCard(false)}
          />,
          document.body
        )}

      {showCreateDeploymentCard &&
        typeof document !== "undefined" &&
        createPortal(
          <CreateDeploymentCardWrapper
            onSubmit={handleOnDeploymentSubmit}
            onClose={() => setShowCreateDeploymentCard(false)}
          />,
          document.body
        )}

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

      <div className="z-[2] w-full sticky pt-7 top-0 border-b-1 border-b-gray-200 bg-white mb-3">
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
                      className="w-full h-7 flex flex-row items-center justify-start p-0 gap-1 shadow-none bg-transparent hover:bg-stone-100 cursor-pointer"
                    >
                      <Rocket className="w-3 h-3" />
                      <span className="p-0 !bg-transparent text-xs">
                        Deploy
                      </span>
                    </Button>
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
                      className="w-full h-7 flex flex-row items-center justify-start gap-1 p-2 shadow-none hover:bg-red-100 cursor-pointer"
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
              <Skeleton className="w-1/3 h-full rounded-lg bg-gray-100" />
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
      <div className="w-full h-fit relative max-w-7xl mx-auto mb-3">
        <div className="h-300 w-full"></div>
        {tab === "Backtests" && (
          <>
            <div className="absolute top-0 left-0 w-full">
              <div className="h-7 relative mb-3">
                <div className="absolute right-0 h-full">
                  <BacktestActions
                    onRefresh={() =>
                      setBacktestRefreshCounter((prev) => prev + 1)
                    }
                    onNewBacktest={() => setShowCreateBacktestCard(true)}
                  />
                </div>
              </div>
              <BacktestsTable
                versionId={versionId!}
                refreshCounter={backtestRefreshCounter}
              />
            </div>
          </>
        )}
        {/* {tab === "Deployments" && <DeploymentsTable versionId={versionId!} />} */}
        {tab === "Deployments" && (
          <>
            <div className="absolute top-0 left-0 w-full">
              <div className="w-full h-7 relative mb-3">
                <div className="absolute right-0 h-full">
                  <DeploymentsActions
                    onRefresh={() =>
                      setBacktestRefreshCounter((prev) => prev + 1)
                    }
                    onNewDeployment={() => setShowCreateDeploymentCard(true)}
                  />
                </div>
              </div>
              <DeploymentsTable
                versionId={versionId!}
                refreshCounter={backtestRefreshCounter}
              />
            </div>
          </>
        )}
        {tab === "Positions" && <PositionsTable versionId={versionId!} />}
      </div>
    </DashboardLayout>
  );
};

export default StrategyVersionPage;
