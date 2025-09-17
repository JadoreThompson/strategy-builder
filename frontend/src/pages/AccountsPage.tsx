import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { HTTP_BASE_URL } from "@/config";
import { useAccountsQuery } from "@/hooks/accounts-hooks";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import type { AccountResponse } from "@/lib/types/accountResponse";
import dayjs from "dayjs";
import { Ellipsis, Pencil, Search, Trash2 } from "lucide-react";
import { useState, type FC } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router";

interface AccountDetailResponse extends AccountResponse {
  login: string;
  server: string;
}

const AccountFormModal: FC<{
  initialData?: AccountDetailResponse | null;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ initialData, onClose, onSuccess }) => {
  const isEditing = !!initialData;

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const body: { [key: string]: any } = Object.fromEntries(formData.entries());

    // Don't send an empty password on update unless it's explicitly changed
    if (isEditing && !body.password) {
      delete body.password;
    }

    const url = isEditing
      ? `${HTTP_BASE_URL}/accounts/${initialData.account_id}`
      : `${HTTP_BASE_URL}/accounts`;

    const method = isEditing ? "PATCH" : "POST";

    try {
      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to ${method} account.`);
      }

      onSuccess();
    } catch (error) {
      console.error("Failed to submit account:", error);
      alert(
        `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    }
  };

  return (
    <Card className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-lg">
        <h2 className="mb-4 text-lg font-bold">
          {isEditing ? "Update Account" : "Create Account"}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Name</label>
            <Input
              type="text"
              name="name"
              defaultValue={initialData?.name}
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
              defaultValue={initialData?.login}
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
                isEditing ? "Leave blank to keep unchanged" : "••••••••"
              }
              className="w-full rounded-md border px-3 py-2"
              required={!isEditing}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Server</label>
            <Input
              type="text"
              name="server"
              defaultValue={initialData?.server}
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
              defaultValue={initialData?.platform || "mt5"}
              required
            >
              <option value="mt5">MT5</option>
            </select>
          </div>
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
  account: AccountResponse;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ account, onClose, onSuccess }) => {
  const [confirmationText, setConfirmationText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    try {
      const rsp = await fetch(
        `${HTTP_BASE_URL}/accounts/${account.account_id}`,
        {
          method: "DELETE",
          credentials: "include",
        },
      );

      if (!rsp.ok) {
        const data = await rsp.json();
        throw new Error(data.error || "Failed to delete account");
      }

      onSuccess();
    } catch (error) {
      console.error("Failed to delete account:", error);
      setError(`${error instanceof Error ? error.message : "Unknown error"}`);
    }
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
        {error && (
          <span className="text-sm font-semibold text-red-500">{error}</span>
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
  const [isDeleting, setIsDeleting] = useState<boolean | null>(false);

  const [curAccount, setCurAccount] = useState<
    AccountDetailResponse | undefined
  >(undefined);

  const accountsQuery = useAccountsQuery({ name: searchText });

  const handleSuccess = () => {
    setIsCreating(false);
    setIsEditing(false);
    setIsDeleting(false);
    setCurAccount(undefined);
    accountsQuery.refetch();
  };

  return (
    <DashboardLayout>
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
            initialData={curAccount}
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
        <Table className="border-1 border-gray-300">
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
            {accountsQuery.data ? (
              accountsQuery.data.map((acc, idx) => (
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
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} className="h-25">
                  <div className="flex h-full w-full items-center justify-center">
                    {accountsQuery.isPending ? (
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
      </div>
      <Link to={""} />
    </DashboardLayout>
  );
};

export default AccountsPage;
