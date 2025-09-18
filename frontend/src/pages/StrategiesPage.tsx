import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useStrategiesQuery } from "@/hooks/strategies-hooks";
import { DashboardLayout } from "@/layouts/dashboard-layout";
import dayjs from "dayjs";
import { Search } from "lucide-react";
import { useState, type FC } from "react";
import { Link, useNavigate } from "react-router";

const StrategiesPage: FC = () => {
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState("");

  const strategiesQuery = useStrategiesQuery({
    name: searchText,
  });

  return (
    <DashboardLayout>
      <h1 className="mb-3 text-2xl font-semibold">Strategies</h1>
      <div className="mb-3 flex h-9 w-full justify-between">
        <Link
          to="/create-strategy"
          className="bg-primary flex h-full w-20 cursor-pointer items-center justify-center p-1 text-sm font-medium text-white"
        >
          Create
        </Link>
        <div className="flex h-full items-center border-1 border-gray-200 px-2">
          <Search className="h-5 w-5 text-gray-600" />
          <Input
            placeholder="Search"
            className="border-none focus:!ring-0"
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
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {strategiesQuery.data ? (
              strategiesQuery.data.map((strat, idx) => (
                <TableRow
                  key={idx}
                  onClick={() => navigate(`/strategies/${strat.strategy_id}`)}
                  className="cursor-pointer"
                >
                  <TableCell>{`${strat.strategy_id.slice(0, 8)}...`}</TableCell>
                  <TableCell>{strat.name}</TableCell>
                  <TableCell>
                    {dayjs(strat.created_at).format("YYYY-MM-DD")}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={3} className="h-25">
                  <div className="flex h-full w-full items-center justify-center">
                    {strategiesQuery.isPending ? (
                      <>
                        Loading <p className="ellipsis"></p>
                      </>
                    ) : (
                      <>
                        {searchText
                          ? "No strategy found"
                          : "It seems you have no strategies. Better lock in."}
                      </>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </DashboardLayout>
  );
};

export default StrategiesPage;
