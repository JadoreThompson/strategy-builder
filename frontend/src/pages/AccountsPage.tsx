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
import useFetch from "@/hooks/useFetch";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import type { AccountResponse } from "@/lib/types/accountResponse";
import { Ellipsis, Pencil, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState, type FC } from "react";
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
        `Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    }
  };

  return (
    <Card className="z-50 fixed inset-0 flex items-center justify-center bg-black/30">
      <div className="bg-white p-6 rounded-md shadow-lg w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">
          {isEditing ? "Update Account" : "Create Account"}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <Input
              type="text"
              name="name"
              defaultValue={initialData?.name}
              placeholder="My Trading Account"
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Login</label>
            <Input
              type="text"
              name="login"
              defaultValue={initialData?.login}
              placeholder="123456"
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <Input
              type="password"
              name="password"
              placeholder={
                isEditing ? "Leave blank to keep unchanged" : "••••••••"
              }
              className="w-full border rounded-md px-3 py-2"
              required={!isEditing}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Server</label>
            <Input
              type="text"
              name="server"
              defaultValue={initialData?.server}
              placeholder="Broker-Server"
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Platform</label>
            <select
              name="platform"
              className="w-full border rounded-md px-3 py-2 bg-white"
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
        }
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
    <Card className="z-50 fixed inset-0 flex items-center justify-center bg-black/30">
      <div className="bg-white p-6 rounded-md shadow-lg w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">Delete Account</h2>
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
          <span className="text-red-500 text-sm font-semibold">{error}</span>
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
  const [showCreateCard, setShowCreateCard] = useState<boolean>(false);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean | null>(false);
  const [focusedAcc, setFocusedAcc] = useState<AccountResponse | null>(null);
  const [editingAccount, setEditingAccount] =
    useState<AccountDetailResponse | null>(null);

  const [refetchTrigger, setRefetchTrigger] = useState<number>(0);

  const url = useMemo(() => {
    const params = new URLSearchParams();
    if (searchText) {
      params.append("name", searchText);
    }
    params.append("_", String(refetchTrigger));
    return `${HTTP_BASE_URL}/accounts?${params.toString()}`;
  }, [searchText, refetchTrigger]);

  const { data, loading: isLoading } = useFetch<AccountResponse[]>(url, {
    credentials: "include",
  });

  const accounts = useMemo(() => {
    if (data) {
      return data.map((d) => ({
        ...d,
        created_at: new Date(d.created_at).toISOString().split("T")[0],
      }));
    } else {
      return [];
    }
  }, [data]);

  useEffect(() => {
    if (isEditing && focusedAcc) {
      (async () => {
        const rsp = await fetch(
          HTTP_BASE_URL + `/accounts/${focusedAcc.account_id}`,
          { credentials: "include" }
        );

        if (rsp.ok) {
          const data: AccountDetailResponse = await rsp.json();
          setEditingAccount(data);
        }
      })();
    }
  }, [isEditing, focusedAcc]);

  const handleSuccess = () => {
    setShowCreateCard(false);
    setIsEditing(false);
    setIsDeleting(false);
    setFocusedAcc(null);
    setEditingAccount(null);
    setRefetchTrigger((t) => t + 1);
  };

  return (
    <DashboardLayout>
      {showCreateCard &&
        createPortal(
          <AccountFormModal
            onClose={() => setShowCreateCard(false)}
            onSuccess={handleSuccess}
          />,
          document.body
        )}
      {editingAccount &&
        createPortal(
          <AccountFormModal
            initialData={editingAccount}
            onClose={() => {
              setIsEditing(false);
              setFocusedAcc(null);
              setEditingAccount(null);
            }}
            onSuccess={handleSuccess}
          />,
          document.body
        )}
      {isDeleting &&
        focusedAcc &&
        createPortal(
          <DeleteConfirmationModal
            account={focusedAcc}
            onClose={() => {
              setIsDeleting(false);
              setFocusedAcc(null);
            }}
            onSuccess={handleSuccess}
          />,
          document.body
        )}

      <h1 className="text-2xl font-semibold mb-3">Accounts</h1>
      <div className="w-full h-9 flex justify-between mb-3">
        <Button
          onClick={() => setShowCreateCard(true)}
          className="h-full w-fit flex items-center justify-center bg-primary text-white text-sm font-medium p-1 cursor-pointer"
        >
          Add Account
        </Button>
        <div className="h-full flex items-center border-1 border-gray-200 px-2">
          <Search className="text-gray-600 w-5 h-full" />
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
            {accounts.length ? (
              accounts.map((acc, idx) => (
                <TableRow key={idx}>
                  <TableCell className="cursor-pointer">
                    {`${acc.account_id.slice(0, 8)}...`}
                  </TableCell>
                  <TableCell className="cursor-pointer">{acc.name}</TableCell>
                  <TableCell className="cursor-pointer">
                    {acc.platform}
                  </TableCell>
                  <TableCell className="cursor-pointer">
                    {acc.created_at}
                  </TableCell>
                  <TableCell
                    className="text-right"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <span className="sr-only">Open menu</span>
                          <Ellipsis className="h-4 w-4" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent align="end" className="w-30 p-1">
                        <Button
                          variant="ghost"
                          onClick={() => {
                            setFocusedAcc(acc), setIsEditing(true);
                          }}
                          className="w-full justify-start font-normal text-xs cursor-pointer"
                        >
                          <Pencil className="mr-1 h-3 w-3" />
                          Update
                        </Button>
                        <Button
                          variant="ghost"
                          onClick={() => {
                            setFocusedAcc(acc), setIsDeleting(true);
                          }}
                          className="w-full justify-start font-normal text-xs text-red-600 hover:text-red-600 hover:bg-red-100 cursor-pointer"
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
                  <div className="w-full h-full flex items-center justify-center">
                    {isLoading ? (
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
