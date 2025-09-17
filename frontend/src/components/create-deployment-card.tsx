import type { AccountResponse } from "@/lib/types/accountResponse";
import type { FC } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Skeleton } from "./ui/skeleton";

export interface CreateDeploymentCardProps {
  accounts: AccountResponse[];
  loading: boolean;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void | Promise<void>;
  onClose: () => void | Promise<void>;
}

const CreateDeploymentCard: FC<CreateDeploymentCardProps> = ({
  accounts,
  loading,
  onSubmit,
  onClose,
}) => {
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

export default CreateDeploymentCard;
