import type { FC } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";

const CreateBacktestCard: FC<{
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void | Promise<void>;
  onClose: () => void | Promise<void>;
}> = ({ onSubmit, onClose }) => {
  return (
    <Card className="z-50 fixed inset-0 flex items-center justify-center bg-black/30">
      <div className="bg-white p-6 rounded-md shadow-lg w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">Launch Backtest</h2>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Instrument</label>
            <Input
              type="text"
              name="instrument"
              placeholder="e.g. BTC/USDT"
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Starting Balance
            </label>
            <Input
              type="number"
              name="starting_balance"
              placeholder="1000"
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Leverage</label>
            <Input
              type="number"
              name="leverage"
              placeholder="10"
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onClose()}
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

export default CreateBacktestCard;
