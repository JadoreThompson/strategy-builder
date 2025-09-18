import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateStrategyMutation } from "@/hooks/strategies-hooks";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { useEffect, useState, type FC } from "react";
import { useNavigate, useSearchParams } from "react-router";

const CreateVersionPage: FC = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const createStrategyMutation = useCreateStrategyMutation();

  const [strategyId, setStrategyId] = useState<string | undefined>(undefined);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");

  useEffect(() => {
    const sid = params.get("strategy_id");

    if (!sid) {
      navigate("/strategies");
    } else {
      setStrategyId(sid);
    }
  }, [params]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    createStrategyMutation
      .mutateAsync({ strategy_id: strategyId, name, prompt })
      .then((data) => navigate(`/strategies/versions/${data.version_id}`));
  };

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-2xl p-6">
        <h1 className="mb-4 text-2xl font-bold">Create a New Version</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">
              Version Name
            </label>
            <Input
              type="text"
              placeholder="Enter version name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border px-3 py-2 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">
              Version Prompt
            </label>
            <textarea
              placeholder="Describe the version..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={5}
              required
              className="h-75 w-full resize-none rounded-md border px-3 py-2 focus:outline-none"
            />
          </div>

          {createStrategyMutation.error && (
            <div className="w-full text-center">
              <span className="font-semibold text-red-500">
                {createStrategyMutation.error.message}
              </span>
            </div>
          )}

          <Button
            type="submit"
            disabled={createStrategyMutation.isPending || !name || !prompt}
            className="w-full cursor-pointer rounded-md px-4 py-2 text-white disabled:bg-gray-900"
          >
            {createStrategyMutation.isPending
              ? "Creating..."
              : "Create Version"}
          </Button>
        </form>
      </div>
    </DashboardLayout>
  );
};

export default CreateVersionPage;
