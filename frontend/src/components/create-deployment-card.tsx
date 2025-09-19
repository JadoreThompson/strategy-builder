import { useInfiniteAccountsQuery } from "@/hooks/accounts-hooks";
import useIntersectionObserver from "@/hooks/intersection-observer";
import type { FC } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Skeleton } from "./ui/skeleton";

export interface CreateDeploymentCardProps {
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void | Promise<void>;
  onClose: () => void | Promise<void>;
}

const CreateDeploymentCard: FC<CreateDeploymentCardProps> = ({
  onSubmit,
  onClose,
}) => {
  const infiniteAccountsQuery = useInfiniteAccountsQuery();
  const optionsFooterIntersectionObserver =
    useIntersectionObserver<HTMLOptionElement>(() => {
      const pages = infiniteAccountsQuery.data?.pages || [];
      if (!pages.length || pages[pages.length - 1].has_next) {
        infiniteAccountsQuery.fetchNextPage();
      }
    });

  const foundAccounts =
    infiniteAccountsQuery.data &&
    infiniteAccountsQuery.data.pages.length &&
    infiniteAccountsQuery.data.pages[0].size;

  return (
    <Card className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-lg">
        <h2 className="mb-4 text-lg font-bold">Launch Deployment</h2>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label htmlFor="" className="mb-1 block text-sm font-medium">
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
              className="mb-1 block text-sm font-medium"
            >
              Account
            </label>
            {infiniteAccountsQuery.isPending ? (
              <Skeleton className="h-10 w-full bg-gray-100" />
            ) : (
              <select
                id="account_id"
                name="account_id"
                className="w-full rounded-md border px-3 py-2"
                required
                defaultValue=""
              >
                <option value="" disabled>
                  Select an account
                </option>
                {infiniteAccountsQuery.data?.pages.map((page) =>
                  page.data.map((acc) => (
                    <option key={acc.account_id} value={acc.account_id}>
                      {acc.name}
                    </option>
                  )),
                )}
                <option ref={optionsFooterIntersectionObserver.elementRefObj}>
                  Hy
                </option>
              </select>
            )}
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
              disabled={!foundAccounts}
            >
              Submit
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
};

export default CreateDeploymentCard;
