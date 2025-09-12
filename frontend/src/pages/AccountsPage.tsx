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
import { HTTP_BASE_URL } from "@/config";
import useFetch from "@/hooks/useFetch";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Search } from "lucide-react";
import { useMemo, useState, type FC } from "react";
import { createPortal } from "react-dom";
import { Link, useNavigate } from "react-router";

interface AccountResponse {
  account_id: string;
  name: string;
  platform: string;
  created_at: string;
}

const CreateAccountCard: FC<{
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void | Promise<void>;
  setShowCard: (arg: boolean) => void | Promise<void>;
}> = ({ handleSubmit, setShowCard }) => {
  return (
    <Card className="z-50 fixed inset-0 flex items-center justify-center bg-black/30">
      <div className="bg-white p-6 rounded-md shadow-lg w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">Create Account</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              name="name"
              placeholder="My Trading Account"
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Login</label>
            <input
              type="text"
              name="login"
              placeholder="123456"
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              name="password"
              placeholder="••••••••"
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Server</label>
            <input
              type="text"
              name="server"
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
              defaultValue="mt5"
              required
            >
              <option value="mt5">MT5</option>
            </select>
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
    </Card>
  );
};

const AccountsPage: FC = () => {
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState<string>("");
  const [showCard, setShowCard] = useState<boolean>(false);

  const { data, loading: isLoading } = useFetch<AccountResponse[]>(
    HTTP_BASE_URL +
      "/accounts" +
      (searchText ? `?name=${encodeURIComponent(searchText)}` : ""),
    {
      credentials: "include",
    }
  );

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

  return (
    <DashboardLayout>
      {showCard &&
        typeof document !== "undefined" &&
        createPortal(
          <CreateAccountCard
            handleSubmit={(e) => {}}
            setShowCard={setShowCard}
          />,
          document.body
        )}
      <h1 className="text-2xl font-semibold mb-3">Accounts</h1>
      <div className="w-full h-9 flex justify-between mb-3">
        <Button
          onClick={() => setShowCard(true)}
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
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.length ? (
              accounts.map((acc, idx) => (
                <TableRow
                  key={idx}
                  onClick={() => navigate(`/accounts/${acc.account_id}`)}
                  className="cursor-pointer"
                >
                  <TableCell>{`${acc.account_id.slice(0, 8)}...`}</TableCell>
                  <TableCell>{acc.name}</TableCell>
                  <TableCell>{acc.platform}</TableCell>
                  <TableCell>{acc.created_at}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="h-25">
                  <div className="w-full h-full flex items-center justify-center">
                    {isLoading ? (
                      <>
                        Loading <p className="ellipsis"></p>
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
