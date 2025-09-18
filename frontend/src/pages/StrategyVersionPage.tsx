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
import { useAccountsQuery } from "@/hooks/accounts-hooks";
import { useCreateDeploymentMutation } from "@/hooks/deployments-hooks";
import {
  useBacktestsQuery,
  useCreateBacktestMutation,
  useDeleteStrategyVersionMutation,
  useStrategyVersionQuery,
} from "@/hooks/strategy-version-hooks";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import type { BacktestCreate } from "@/openapi";
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
    <div className="flex h-full gap-3">
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
    <div className="flex h-full gap-3">
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
  const accountsQuery = useAccountsQuery();

  return (
    <CreateDeploymentCard
      accounts={accountsQuery.data || []}
      loading={accountsQuery.isPending}
      onSubmit={onSubmit}
      onClose={onClose}
    />
  );
};

const TABS = ["Backtests", "Deployments", "Positions"] as const;
type Tab = (typeof TABS)[number];

const DEFAULT_TAB = TABS[0];

const StrategyVersionPage: FC = () => {
  const { versionId } = useParams();
  const navigate = useNavigate();

  const strategyVersionQuery = useStrategyVersionQuery(versionId!);
  const createBacktestMutation = useCreateBacktestMutation();
  const createDeploymentMutation = useCreateDeploymentMutation();
  const deleteStrategyVersionMutation = useDeleteStrategyVersionMutation();
  const backtestsQuery = useBacktestsQuery(versionId!);

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
    deleteStrategyVersionMutation
      .mutateAsync({
        strategyId: strategyVersionQuery.data!.strategy_id,
        versionId: strategyVersionQuery.data!.version_id,
      })
      .then(() =>
        navigate(`/strategies/${strategyVersionQuery.data!.strategy_id}`),
      )
      .catch((err) => toast(`Error: ${err.message}`));
  };

  const handleOnBacktestSubmit = async (
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();

    const body: BacktestCreate = Object.fromEntries(
      new FormData(e.currentTarget).entries(),
    );

    createBacktestMutation
      .mutateAsync({ versionId: versionId!, data: body })
      .then(() => {
        toast("Backtest initiated");
        backtestsQuery.refetch();
      })
      .catch((err) => toast(`Error: ${err.message}`));

    setShowCreateBacktestCard(false);
  };

  const handleOnDeploymentSubmit = async (
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();

    const fd = new FormData(e.currentTarget);
    const account_id = fd.get("account_id") as string;
    const instrument = fd.get("instrument") as string;

    if (!account_id || !instrument) {
      toast("Please provide both an account and an instrument.");
      return;
    }

    createDeploymentMutation
      .mutateAsync({
        account_id,
        version_id: versionId!,
        instrument,
      })
      .then(() => toast("Deployment initiated successfully."))
      .catch((err) => toast(`Error: ${err.message}`));

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
          document.body,
        )}

      {showCreateDeploymentCard &&
        typeof document !== "undefined" &&
        createPortal(
          <CreateDeploymentCardWrapper
            onSubmit={handleOnDeploymentSubmit}
            onClose={() => setShowCreateDeploymentCard(false)}
          />,
          document.body,
        )}

      {showPrompt &&
        strategyVersionQuery.data &&
        typeof document !== "undefined" &&
        createPortal(
          <div className="fixed inset-0 z-[999] flex items-center justify-center bg-black/30 backdrop-blur-sm">
            <Card className="relative max-h-[600px] min-h-[300px] w-full max-w-2xl border border-gray-200 p-6 shadow-xl">
              <h2 className="mb-4 text-xl font-semibold">Prompt</h2>
              <div className="prose prose-sm h-full min-h-[300px] w-full overflow-y-scroll whitespace-pre-wrap text-gray-700">
                {strategyVersionQuery.data.prompt}
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
          document.body,
        )}

      <div className="sticky top-0 z-[2] mb-3 w-full border-b-1 border-b-gray-200 bg-white pt-7">
        <div className="mx-auto max-w-7xl">
          <div className="mb-3 h-7 w-full">
            {!strategyVersionQuery.isPending && strategyVersionQuery.data ? (
              <div className="flex h-full w-full justify-between">
                <h1 className="text-2xl font-semibold">
                  {strategyVersionQuery.data.name}
                </h1>
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
                      className="cursor-pointer !bg-transparent shadow-none"
                    >
                      <Ellipsis />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent
                    className="z-50 flex w-30 flex-col gap-1 p-1"
                    side="bottom"
                    align="end"
                    forceMount
                  >
                    <Button
                      variant="secondary"
                      className="flex h-7 w-full cursor-pointer flex-row items-center justify-start gap-1 bg-transparent p-0 shadow-none hover:bg-stone-100"
                    >
                      <Rocket className="h-3 w-3" />
                      <span className="!bg-transparent p-0 text-xs">
                        Deploy
                      </span>
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => setShowPrompt(true)}
                      className="flex h-7 w-full cursor-pointer flex-row items-center justify-start gap-1 bg-transparent p-0 shadow-none hover:bg-stone-100"
                    >
                      <NotepadText className="h-3 w-3" />
                      <span className="!bg-transparent p-0 text-xs">
                        Prompt
                      </span>
                    </Button>
                    <Button
                      variant="secondary"
                      className="flex h-7 w-full cursor-pointer flex-row items-center justify-start gap-1 bg-transparent p-2 shadow-none hover:bg-stone-100"
                    >
                      <MessageCircle className="h-3 w-3" />
                      <span className="!bg-transparent p-0 text-xs">Chat</span>
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => deleteVersion()}
                      className="flex h-7 w-full cursor-pointer flex-row items-center justify-start gap-1 p-2 shadow-none hover:bg-red-100"
                    >
                      <Trash2 className="h-3 w-3 text-red-500" />
                      <span className="!bg-transparent p-0 text-xs text-red-500">
                        Delete
                      </span>
                    </Button>
                  </PopoverContent>
                </Popover>
              </div>
            ) : (
              <Skeleton className="h-full w-1/3 rounded-lg bg-gray-100" />
            )}
          </div>
          <div className="flex h-fit w-full flex-row justify-start gap-1">
            {TABS.map((t) => (
              <Button
                key={t}
                variant="secondary"
                onClick={() => setTab(t)}
                className={`cursor-pointer rounded-none border-b-2 !bg-transparent shadow-none ${
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
      <div className="relative mx-auto mb-3 h-fit w-full max-w-7xl">
        <div className="h-300 w-full"></div>
        {tab === "Backtests" && (
          <>
            <div className="absolute top-0 left-0 w-full">
              <div className="relative mb-3 h-7">
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
        {tab === "Deployments" && (
          <>
            <div className="absolute top-0 left-0 w-full">
              <div className="relative mb-3 h-7 w-full">
                <div className="absolute right-0 h-full">
                  <DeploymentsActions
                    onRefresh={() =>
                      setDeploymentRefreshCounter((prev) => prev + 1)
                    }
                    onNewDeployment={() => setShowCreateDeploymentCard(true)}
                  />
                </div>
              </div>
              <DeploymentsTable
                versionId={versionId!}
                refreshCounter={deploymentRefreshCounter}
              />
            </div>
          </>
        )}
        {tab === "Positions" && (
          <>
            <div className="absolute top-0 left-0 w-full">
              <PositionsTable versionId={versionId!} />
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
};

export default StrategyVersionPage;
