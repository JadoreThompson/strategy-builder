import ScrollTop from "@/components/scroll-top";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useCreateAccountMutation,
  useDeleteAccountMutation,
  useInfiniteAccountsQuery,
  useUpdateAccountMutation,
} from "@/hooks/accounts-hooks";
import useIntersectionObserver from "@/hooks/intersection-observer";
import { DashboardLayout } from "@/layouts/dashboard-layout";
import { queryClient } from "@/lib/query/query-client";

import type {
  AccountCreate,
  AccountDetailResponse,
  AccountUpdate,
} from "@/openapi";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@radix-ui/react-popover";
import dayjs from "dayjs";
import { Ellipsis, Pencil, Search, Trash2 } from "lucide-react";
import { useEffect, useState, type FC } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router";

const AccountFormModal: FC<{
  accountData?: AccountDetailResponse | null;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ accountData, onClose, onSuccess }) => {
  const isUpdating = !!accountData;

  const createAccountMutation = useCreateAccountMutation();
  const updateAccountMutation = useUpdateAccountMutation();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const body: { [key: string]: any } = Object.fromEntries(formData.entries());

    // Don't send an empty password on update unless it's explicitly changed
    if (isUpdating && !body.password) {
      delete body.password;
      updateAccountMutation
        .mutateAsync({
          accountId: accountData.account_id,
          data: body as AccountUpdate,
        })
        .then(onSuccess);
    } else {
      createAccountMutation.mutateAsync(body as AccountCreate).then(onSuccess);
    }
  };

  return (
    <Card className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-lg">
        <h2 className="mb-4 text-lg font-bold">
          {isUpdating ? "Update Account" : "Create Account"}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Name</label>
            <Input
              type="text"
              name="name"
              defaultValue={accountData?.name}
              placeholder="My Trading Account"
              className="w-full rounded-md border px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Login</label>
            <Input
              type="text"
              name="login"
              defaultValue={accountData?.login}
              placeholder="123456"
              className="w-full rounded-md border px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Password</label>
            <Input
              type="password"
              name="password"
              placeholder={
                isUpdating ? "Leave blank to keep unchanged" : "••••••••"
              }
              className="w-full rounded-md border px-3 py-2"
              required={!isUpdating}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Server</label>
            <Input
              type="text"
              name="server"
              defaultValue={accountData?.server}
              placeholder="Broker-Server"
              className="w-full rounded-md border px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Platform</label>
            <select
              name="platform"
              className="w-full rounded-md border bg-white px-3 py-2"
              defaultValue={accountData?.platform || "mt5"}
              required
            >
              <option value="mt5">MT5</option>
            </select>
          </div>
          {isUpdating && updateAccountMutation.error && (
            <div className="flex items-center justify-center">
              <span className="text-center text-red-500">
                {updateAccountMutation.error.message}
              </span>
            </div>
          )}
          {!isUpdating && createAccountMutation.error && (
            <div className="flex items-center justify-center">
              <span className="text-center text-red-500">
                {createAccountMutation.error.message}
              </span>
            </div>
          )}
          <div className="flex justify-end space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="cursor-pointer rounded-md border border-gray-300 px-4 py-2 text-sm"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="cursor-pointer rounded-md px-4 py-2 text-white"
            >
              Submit
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
};

const DeleteConfirmationModal: FC<{
  account: AccountDetailResponse;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ account, onClose, onSuccess }) => {
  const [confirmationText, setConfirmationText] = useState("");
  const deleteAccountMutation = useDeleteAccountMutation();

  const handleDelete = async () => {
    deleteAccountMutation.mutateAsync(account.account_id).then(onSuccess);
  };

  return (
    <Card className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-lg">
        <h2 className="mb-4 text-lg font-bold">Delete Account</h2>
        <p className="mb-4 text-sm">
          This action cannot be undone. To confirm, please type{" "}
          <strong className="text-red-600">{account.name}</strong> in the box
          below.
        </p>
        <Input
          value={confirmationText}
          onChange={(e) => setConfirmationText(e.target.value)}
          placeholder={account.name}
          className="mb-4"
        />
        {deleteAccountMutation.error && (
          <span className="text-sm font-semibold text-red-500">
            {deleteAccountMutation.error.message}
          </span>
        )}
        <div className="flex justify-end space-x-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={confirmationText !== account.name}
          >
            Confirm
          </Button>
        </div>
      </div>
    </Card>
  );
};

const AccountsPage: FC = () => {
  const [searchText, setSearchText] = useState<string>("");
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [curAccount, setCurAccount] = useState<
    AccountDetailResponse | undefined
  >(undefined);

  const infiniteAccountsQuery = useInfiniteAccountsQuery({
    name: searchText,
  });
  const tableFooterIntersectionObserver =
    useIntersectionObserver<HTMLDivElement>(() => {
      const pages = infiniteAccountsQuery.data?.pages || [];
      if (!pages.length || pages[pages.length - 1].has_next) {
        infiniteAccountsQuery.fetchNextPage();
      }
    });

  useEffect(() => {
    queryClient.clear();
  }, [searchText]);

  const handleSuccess = () => {
    setIsCreating(false);
    setIsEditing(false);
    setIsDeleting(false);
    setCurAccount(undefined);
    infiniteAccountsQuery.refetch();
  };

  return (
    <DashboardLayout>
      <ScrollTop />

      {isCreating &&
        createPortal(
          <AccountFormModal
            onClose={() => setIsCreating(false)}
            onSuccess={handleSuccess}
          />,
          document.body,
        )}

      {isEditing &&
        curAccount &&
        createPortal(
          <AccountFormModal
            accountData={curAccount}
            onClose={() => {
              setIsEditing(false);
              setCurAccount(undefined);
            }}
            onSuccess={handleSuccess}
          />,
          document.body,
        )}

      {isDeleting &&
        curAccount &&
        createPortal(
          <DeleteConfirmationModal
            account={curAccount}
            onClose={() => {
              setIsDeleting(false);
              setCurAccount(undefined);
            }}
            onSuccess={handleSuccess}
          />,
          document.body,
        )}

      <h1 className="mb-3 text-2xl font-semibold">Accounts</h1>
      <div className="mb-3 flex h-9 w-full justify-between">
        <Button
          onClick={() => setIsCreating(true)}
          className="bg-primary flex h-full w-fit cursor-pointer items-center justify-center p-1 text-sm font-medium text-white"
        >
          Add Account
        </Button>
        <div className="flex h-full items-center border-1 border-gray-200 px-2">
          <Search className="h-full w-5 text-gray-600" />
          <Input
            placeholder="Search"
            className="h-full border-none focus:!ring-0"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </div>
      </div>
      <div className="border-gray-300">
        <Table className="mb-3 border-1 border-gray-300">
          <TableHeader>
            <TableRow>
              <TableHead className="w-30">ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Platform</TableHead>
              <TableHead>Created</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {infiniteAccountsQuery.data?.pages ? (
              infiniteAccountsQuery.data.pages.map((pagi) =>
                pagi.data.map((acc, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="cursor-pointer">
                      {`${acc.account_id.slice(0, 8)}...`}
                    </TableCell>
                    <TableCell className="cursor-pointer">{acc.name}</TableCell>
                    <TableCell className="cursor-pointer">
                      {acc.platform}
                    </TableCell>
                    <TableCell className="cursor-pointer">
                      {dayjs(acc.created_at).format("YYYY-MM")}
                    </TableCell>
                    <TableCell
                      className="text-right"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="ghost"
                            className="h-8 w-8 cursor-pointer p-0"
                          >
                            <span className="sr-only">Open menu</span>
                            <Ellipsis className="h-4 w-4" />
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent align="end" className="w-30 p-1">
                          <Button
                            variant="ghost"
                            onClick={() => {
                              (setCurAccount(acc), setIsEditing(true));
                            }}
                            className="w-full cursor-pointer justify-start text-xs font-normal"
                          >
                            <Pencil className="mr-1 h-3 w-3" />
                            Update
                          </Button>
                          <Button
                            variant="ghost"
                            onClick={() => {
                              (setCurAccount(acc), setIsDeleting(true));
                            }}
                            className="w-full cursor-pointer justify-start text-xs font-normal text-red-600 hover:bg-red-100 hover:text-red-600"
                          >
                            <Trash2 className="mr-1 h-3 w-3" />
                            Delete
                          </Button>
                        </PopoverContent>
                      </Popover>
                    </TableCell>
                  </TableRow>
                )),
              )
            ) : (
              <TableRow>
                <TableCell colSpan={5} className="h-25">
                  <div className="flex h-full w-full items-center justify-center">
                    {infiniteAccountsQuery.isPending ? (
                      <>
                        Loading
                        <p className="ellipsis"></p>
                      </>
                    ) : (
                      <>
                        {searchText
                          ? "No account found"
                          : "It seems you have no accounts. Add one to get started."}
                      </>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <div ref={tableFooterIntersectionObserver.refObj}></div>
        {infiniteAccountsQuery.isFetching &&
          infiniteAccountsQuery.data?.pages.length && (
            <div className="flex h-8 w-full items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-stone-300 border-t-transparent"></div>
            </div>
          )}
      </div>
      <Link to={""} />
    </DashboardLayout>
  );
};

export default AccountsPage;
