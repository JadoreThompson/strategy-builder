import { useStopDeploymentMutation } from "@/hooks/deployments-hooks";
import useIntersectionObserver from "@/hooks/intersection-observer";
import { useInfiniteDeploymentsQuery } from "@/hooks/strategy-version-hooks";
import type { DeploymentStatus } from "@/openapi";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@radix-ui/react-popover";
import { Ellipsis, OctagonX } from "lucide-react";
import { type FC, Fragment, useEffect, useState } from "react";
import { toast } from "sonner";
import Spinner from "./spinner";
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
  onClose: () => void;
  onSubmit: () => void;
}> = ({ onClose, onSubmit }) => {

  const [confirmationText, setConfirmationText] = useState("");
  const [randWord] = useState<string>(getRandomWord(6));


  return (
    <Card className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-lg">
        <h2 className="mb-4 text-lg font-bold">Stop Deployment</h2>
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
            onClick={onSubmit}
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

const DeploymentsTable: FC<{ versionId: string; refreshCounter: number }> = ({
  versionId,
  refreshCounter,
}) => {
  const [deploymentId, setDeploymentId] = useState<string | undefined>(
    undefined,
  );

  const stopDeploymentMutation = useStopDeploymentMutation();
  const infiniteDeploymentsbyVersionQuery =
    useInfiniteDeploymentsQuery(versionId);
  const tableFooterIntersectionObserver =
    useIntersectionObserver<HTMLDivElement>(() => {
      const pages = infiniteDeploymentsbyVersionQuery.data?.pages || [];
      if (!pages.length || pages[pages.length - 1].has_next) {
        infiniteDeploymentsbyVersionQuery.fetchNextPage();
      }
    });

  useEffect(() => {
    infiniteDeploymentsbyVersionQuery.refetch();
  }, [refreshCounter]);

  const allDeployments =
    infiniteDeploymentsbyVersionQuery.data?.pages.flatMap((p) => p.data) || [];

  return (
    <>
      {deploymentId && (
        <StopDeploymentConfirmationModal
          onClose={() => setDeploymentId(undefined)}
          onSubmit={() =>
            stopDeploymentMutation
              .mutateAsync({ deploymentId, versionId })
              .then(() => infiniteDeploymentsbyVersionQuery.refetch())
              .catch((err) => toast(`Error: ${err.message}`))
              .finally(() => setDeploymentId(undefined))
          }
        />
      )}

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
        <TableBody>
          {infiniteDeploymentsbyVersionQuery.isPending ? (
            <TableRow>
              <TableCell colSpan={5} className="h-50">
                <Skeleton className="h-full w-full bg-gray-100" />
              </TableCell>
            </TableRow>
          ) : infiniteDeploymentsbyVersionQuery.isError ? (
            <TableRow>
              <TableCell colSpan={5} className="h-50">
                <div className="flex h-full w-full items-center justify-center">
                  <span>{infiniteDeploymentsbyVersionQuery.error.message}</span>
                </div>
              </TableCell>
            </TableRow>
          ) : allDeployments.length > 0 ? (
            infiniteDeploymentsbyVersionQuery.data.pages.map((page, i) => (
              <Fragment key={i}>
                {page.data.map((d) => (
                  <TableRow key={d.deployment_id}>
                    <TableCell className="max-w-[12ch] truncate font-medium">
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
                            className="h-8 w-8 cursor-pointer !bg-transparent p-0"
                          >
                            <span className="sr-only">Open menu</span>
                            <Ellipsis className="h-4 w-4" />
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent
                          align="end"
                          className="w-fit border-1 border-gray-100 bg-white p-1 shadow-sm"
                        >
                          <Button
                            variant="ghost"
                            className="h-8 w-full cursor-pointer justify-start text-xs font-normal text-red-600 hover:bg-red-50 hover:text-red-600"
                            onClick={() => setDeploymentId(d.deployment_id)}
                            disabled={["pending", "stopped", "failed"].includes(
                              d.status,
                            )}
                          >
                            <OctagonX className="h-3 w-3" />
                            Stop Deployment
                          </Button>
                        </PopoverContent>
                      </Popover>
                    </TableCell>
                  </TableRow>
                ))}
              </Fragment>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={5} className="h-50 !bg-gray-100">
                <div className="flex h-full w-full items-center justify-center">
                  <span>No deployments</span>
                </div>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <div ref={tableFooterIntersectionObserver.elementRefObj} />
      {infiniteDeploymentsbyVersionQuery.isFetchingNextPage && <Spinner />}
    </>
  );
};

export default DeploymentsTable;
