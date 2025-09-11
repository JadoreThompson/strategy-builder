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
import { useEffect, useState, type FC } from "react";
import { Link, useNavigate } from "react-router";

interface StrategiesResponse {
  strategy_id: string;
  name: string;
  created_at: string;
}

const StrategiesPage: FC = () => {
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState("");
  const [strategies, setStrategies] = useState<StrategiesResponse[]>([]);

  // Fetch strategies whenever searchText changes
  const { data, loading: isLoading } = useFetch<StrategiesResponse[]>(
    HTTP_BASE_URL +
      "/strategies" +
      (searchText ? `?name=${encodeURIComponent(searchText)}` : ""),
    {
      credentials: "include",
    }
  );

  useEffect(() => {
    if (data) {
      setStrategies(
        data.map((d) => ({
          ...d,
          created_at: new Date(d.created_at).toISOString().split("T")[0],
        }))
      );
    }
  }, [data]);

  return (
    <DashboardLayout>
      <h1 className="text-2xl font-semibold">Strategies</h1>
      <div className="w-full flex justify-end mb-3">
        <div className="flex items-center border-1 border-gray-200 px-2">
          <Search className="text-gray-600 w-5 h-5" />
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
            {strategies.length ? (
              strategies.map((strat, idx) => (
                <TableRow
                  key={idx}
                  onClick={() => navigate(`/strategies/${strat.strategy_id}`)}
                  className="cursor-pointer"
                >
                  <TableCell>{`${strat.strategy_id.slice(0, 8)}...`}</TableCell>
                  <TableCell>{strat.name}</TableCell>
                  <TableCell>{strat.created_at}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={3} className="h-25">
                  <div className="w-full h-full flex items-center justify-center">
                    {isLoading ? (
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
      <Link to={""} />
    </DashboardLayout>
  );
};

export default StrategiesPage;
