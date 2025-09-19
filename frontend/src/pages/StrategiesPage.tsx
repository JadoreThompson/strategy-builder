import ScrollTop from "@/components/scroll-top";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import useIntersectionObserver from "@/hooks/intersection-observer";
import { useInfiniteStrategiesQuery } from "@/hooks/strategies-hooks";
import { DashboardLayout } from "@/layouts/dashboard-layout";
import { queryClient } from "@/lib/query/query-client";
import dayjs from "dayjs";
import { Search } from "lucide-react";
import { useEffect, useState, type FC } from "react";
import { Link, useNavigate } from "react-router";

const StrategiesPage: FC = () => {
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState("");

  const infiniteStrategiesQuery = useInfiniteStrategiesQuery({
    name: searchText,
  });

  const tableFooterIntersectionObserver =
    useIntersectionObserver<HTMLDivElement>(() => {
      const pages = infiniteStrategiesQuery.data?.pages || [];
      if (!pages.length || pages[pages.length - 1].has_next) {
        infiniteStrategiesQuery.fetchNextPage();
      }
    });

  useEffect(() => {
    queryClient.clear();
  }, [searchText]);

  return (
    <DashboardLayout>
      <ScrollTop />
      <h1 className="mb-3 text-2xl font-semibold">Strategies</h1>
      <div className="mb-3 flex h-9 w-full justify-between">
        <Link
          to="/create-strategy"
          className="bg-primary flex h-full w-fit cursor-pointer items-center justify-center p-1 px-3 text-sm font-medium text-white"
        >
          Create
        </Link>
        <div className="flex h-full items-center border-1 border-gray-200 px-2">
          <Search className="h-5 w-5 text-gray-600" />
          <Input
            placeholder="Search"
            className="h-full border-none focus:!ring-0"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </div>
      </div>

      <div className="h-5000 border-gray-300">
        <Table className="mb-3 border-1 border-gray-300">
          <TableHeader>
            <TableRow>
              <TableHead className="w-30">ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {infiniteStrategiesQuery.data?.pages ? (
              infiniteStrategiesQuery.data.pages.map((pagi) =>
                pagi.data.map((strat) => (
                  <TableRow
                    key={strat.strategy_id}
                    onClick={() => navigate(`/strategies/${strat.strategy_id}`)}
                    className="cursor-pointer"
                  >
                    <TableCell>
                      {`${strat.strategy_id.slice(0, 8)}...`}
                    </TableCell>
                    <TableCell>{strat.name}</TableCell>
                    <TableCell>
                      {dayjs(strat.created_at).format("YYYY-MM-DD")}
                    </TableCell>
                  </TableRow>
                )),
              )
            ) : (
              <TableRow>
                <TableCell colSpan={3} className="h-25">
                  <div className="flex h-full w-full items-center justify-center">
                    {infiniteStrategiesQuery.isPending ? (
                      <>
                        Loading
                        <p className="ellipsis"></p>
                      </>
                    ) : (
                      <>
                        {searchText
                          ? "No strategy found"
                          : "It seems you have no strategies. Create one to get started."}
                      </>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <div ref={tableFooterIntersectionObserver.refObj}></div>
        {infiniteStrategiesQuery.isFetching &&
          infiniteStrategiesQuery.data?.pages.length && (
            <div className="flex h-8 w-full items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-stone-300 border-t-transparent"></div>
            </div>
          )}
      </div>
    </DashboardLayout>
  );
};

export default StrategiesPage;
