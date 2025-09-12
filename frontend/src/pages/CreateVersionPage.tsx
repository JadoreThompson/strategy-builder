import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { HTTP_BASE_URL } from "@/config";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { useEffect, useState, type FC } from "react";
import { useNavigate, useSearchParams } from "react-router";

const CreateVersionPage: FC = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [strategyId, setStrategyId] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);

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

    if (!strategyId) return;

    setLoading(true);

    const rsp = await fetch(HTTP_BASE_URL + "/strategies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ name, prompt, strategy_id: strategyId }),
    });

    const data = await rsp.json();

    if (!rsp.ok) {
      setError(data.error);
    } else {
      navigate(`/strategies/versions/${data.version_id}`);
    }

    setLoading(false);
  };

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">Create a New Version</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Version Name
            </label>
            <Input
              type="text"
              placeholder="Enter version name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded-md px-3 py-2 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Version Prompt
            </label>
            <textarea
              placeholder="Describe the version..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={5}
              required
              className="w-full h-75 border rounded-md px-3 py-2 focus:outline-none resize-none"
            />
          </div>

          {error && (
            <div className="w-full text-center">
              <span className="text-red-500 font-semibold">{error}</span>
            </div>
          )}

          <Button
            type="submit"
            disabled={loading || !name || !prompt}
            className="w-full  text-white py-2 px-4 rounded-md disabled:bg-gray-900 cursor-pointer"
          >
            {loading ? "Creating..." : "Create Version"}
          </Button>
        </form>
      </div>
    </DashboardLayout>
  );
};

export default CreateVersionPage;
