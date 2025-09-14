import { HTTP_BASE_URL } from "@/config";
import useFetch from "@/hooks/useFetch";
import type { AccountResponse } from "@/lib/types/accountResponse";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@radix-ui/react-popover";
import { Ellipsis, OctagonX, RotateCw } from "lucide-react";
import { type FC, useState } from "react";
import { createPortal } from "react-dom";
import { toast } from "sonner";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Skeleton } from "./ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

type DeploymentStatus =
  | "not_deployed"
  | "pending"
  | "deployed"
  | "failed"
  | "stopped";

interface Deployment {
  deployment_id: string;
  account_id: string;
  account_name: string;
  version_id: string;
  status: DeploymentStatus;
  created_at: string;
}

const getRandomWord = (length: number) => {
  const chars = "abcdefghijklmnopqrstuvwxyz";
  let result = "";

  for (let i = 0; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * chars.length);
    result += chars[randomIndex];
  }

  return result;
};

const StopDeploymentConfirmationModal: FC<{
  deploymentId: string;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ deploymentId, onClose, onSuccess }) => {
  const [confirmationText, setConfirmationText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [randWord] = useState<string>(getRandomWord(6));

  const handleDelete = async () => {
    try {
      const rsp = await fetch(
        `${HTTP_BASE_URL}/deployments/${deploymentId}/stop`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      if (!rsp.ok) {
        const data = await rsp.json();
        throw new Error(data.error || "Failed to stop deployment");
      }

      onSuccess();
    } catch (error) {
      console.error("Failed to stop deployment:", error);
      setError(`${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  return (
    <Card className="z-50 fixed inset-0 flex items-center justify-center bg-black/30">
      <div className="bg-white p-6 rounded-md shadow-lg w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">Stop Deployment</h2>
        <p className="mb-4 text-sm">
          This action cannot be undone. To confirm, please type{" "}
          <strong className="text-red-600">{randWord}</strong> in the box below.
        </p>
        <Input
          value={confirmationText}
          onChange={(e) => setConfirmationText(e.target.value)}
          placeholder={randWord}
          className="mb-4"
        />
        {error && (
          <span className="text-red-500 text-sm font-semibold">{error}</span>
        )}
        <div className="flex justify-end space-x-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="cursor-pointer"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={confirmationText !== randWord}
            className="cursor-pointer"
          >
            Confirm
          </Button>
        </div>
      </div>
    </Card>
  );
};

const CreateDeploymentCard: FC<{
  accounts: AccountResponse[];
  loading: boolean;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void | Promise<void>;
  onClose: () => void | Promise<void>;
}> = ({ accounts, loading, onSubmit, onClose }) => {
  return (
    <Card className="z-50 fixed inset-0 flex items-center justify-center bg-black/30">
      <div className="bg-white p-6 rounded-md shadow-lg w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">Launch Deployment</h2>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label htmlFor="" className="block text-sm font-medium mb-1">
              Instrument
            </label>
            <Input
              type="text"
              name="instrument"
              placeholder="EURUSD"
              required
            />
          </div>
          <div>
            <label
              htmlFor="account_id"
              className="block text-sm font-medium mb-1"
            >
              Account
            </label>
            {loading ? (
              <Skeleton className="w-full h-10 bg-gray-100" />
            ) : (
              <select
                id="account_id"
                name="account_id"
                className="w-full border rounded-md px-3 py-2"
                required
                defaultValue=""
              >
                <option value="" disabled>
                  Select an account
                </option>
                {accounts.map((acc) => (
                  <option key={acc.account_id} value={acc.account_id}>
                    {acc.name}
                  </option>
                ))}
              </select>
            )}
          </div>
          <div className="flex justify-end space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="px-4 py-2 rounded-md border border-gray-300 text-sm cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="px-4 py-2 text-white rounded-md cursor-pointer"
              disabled={loading || accounts.length === 0}
            >
              Submit
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
};

const DeploymentBadge: FC<{ status: DeploymentStatus; className: string }> = ({
  status,
  className = "",
}) => {
  const getIconColor = (status: DeploymentStatus) => {
    switch (status) {
      case "pending":
        return "bg-orange-200/50 text-orange-500";
      case "deployed":
        return "bg-green-200/50 text-green-500";
      case "failed":
        return "bg-red-200/50 text-red-500";
      case "stopped":
        return "bg-gray-200/50 text-gray-500";
      default:
        return "bg-gray-200/50 text-gray-500";
    }
  };

  return (
    <span className={`${getIconColor(status)} ${className}`}>
      {(() => {
        const s = status.toString();
        return s.charAt(0).toUpperCase() + s.slice(1);
      })()}
    </span>
  );
};

const DeploymentsTable: FC<{ versionId: string }> = ({ versionId }) => {
  const [counter, setCounter] = useState<number>(0);
  const [showCreateCard, setShowCreateCard] = useState<boolean>(false);
  const [showStopDeployment, setShowStopDeployment] = useState<boolean>(false);
  const [deploymentId, setDeploymentId] = useState<string | null>(null);

  const {
    data: deployments,
    loading,
    error,
  } = useFetch<Deployment[]>(
    `${HTTP_BASE_URL}/deployments/by-version/${versionId}?refresh=${counter}`,
    { credentials: "include" }
  );

  const { data: accounts, loading: accountsLoading } = useFetch<
    AccountResponse[]
  >(`${HTTP_BASE_URL}/accounts/`, { credentials: "include" });

  const handleStopDeployment = async (deploymentId: string) => {
    setDeploymentId(deploymentId);
    setShowStopDeployment(true);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
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
      setCounter((prev) => prev + 1);
    } else {
      const data = await rsp.json();
      toast(`Error: ${data.detail || "Failed to create deployment."}`);
    }

    setShowCreateCard(false);
  };

  return (
    <>
      {showCreateCard &&
        typeof document !== "undefined" &&
        createPortal(
          <CreateDeploymentCard
            accounts={accounts || []}
            loading={accountsLoading}
            onSubmit={handleSubmit}
            onClose={() => setShowCreateCard(false)}
          />,
          document.body
        )}

      {showStopDeployment &&
        deploymentId &&
        typeof document !== "undefined" &&
        createPortal(
          <StopDeploymentConfirmationModal
            deploymentId={deploymentId}
            onClose={() => {
              setShowStopDeployment(false);
              setDeploymentId(null);
            }}
            onSuccess={() => {
              setShowStopDeployment(false);
              setDeploymentId(null);
              setCounter((prev) => prev + 1);
            }}
          />,
          document.body
        )}
      <div className="w-full h-7 relative mb-3">
        <div className="h-full absolute right-0 flex gap-3">
          <Button
            variant="outline"
            onClick={() => setCounter((prev) => prev + 1)}
            className="h-full cursor-pointer"
          >
            <RotateCw />
          </Button>
          <Button
            onClick={() => setShowCreateCard(true)}
            className="h-full cursor-pointer"
          >
            Deploy
          </Button>
        </div>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Account ID</TableHead>
            <TableHead>Account Name</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created At</TableHead>
            <TableHead className="text-right"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="text-xs">
          {!loading && !error && (
            <>
              {deployments!.length > 0 ? (
                deployments!.map((d) => (
                  <TableRow key={d.deployment_id}>
                    <TableCell className="font-medium truncate max-w-[12ch]">
                      {d.account_id.slice(0, 8)}...
                    </TableCell>
                    <TableCell>{d.account_name}</TableCell>
                    <TableCell>
                      <DeploymentBadge
                        status={d.status}
                        className="p-1 text-xs"
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(d.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="ghost"
                            className="h-8 w-8 p-0 cursor-pointer !bg-transparent"
                          >
                            <span className="sr-only">Open menu</span>
                            <Ellipsis className="h-4 w-4" />
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent
                          align="end"
                          className="w-fit p-1 border-1 border-gray-100 shadow-sm bg-white"
                        >
                          <Button
                            variant="ghost"
                            className="w-full h-8 justify-start text-xs font-normal hover:bg-red-50 hover:text-red-600 text-red-600 cursor-pointer"
                            onClick={() =>
                              handleStopDeployment(d.deployment_id)
                            }
                            disabled={["pending", "stopped", "failed"].includes(
                              d.status
                            )}
                          >
                            <OctagonX className="w-3 h-3" />
                            Stop Deployment
                          </Button>
                        </PopoverContent>
                      </Popover>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={4} className="h-50 !bg-gray-100">
                    <div className="w-full h-full flex items-center justify-center">
                      <span>No deployments</span>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </>
          )}

          {loading && (
            <TableRow>
              <TableCell colSpan={4} className="h-50">
                <Skeleton className="w-full h-full bg-gray-100" />
              </TableCell>
            </TableRow>
          )}

          {error && (
            <TableRow>
              <TableCell colSpan={4} className="h-50">
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

export default DeploymentsTable;
