import { Button } from "@/components/ui/button";
import { HTTP_BASE_URL } from "@/config";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { useState, type FC } from "react";
import { useNavigate } from "react-router";

const CreateStrategyPage: FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setLoading(true);

    const rsp = await fetch(HTTP_BASE_URL + "/strategies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ name, prompt }),
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
        <h1 className="text-2xl font-bold mb-4">Create a New Strategy</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Strategy Name
            </label>
            <input
              type="text"
              placeholder="Enter strategy name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded-md px-3 py-2 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Strategy Prompt
            </label>
            <textarea
              placeholder="Describe your strategy..."
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
            {loading ? "Creating..." : "Create Strategy"}
          </Button>
        </form>
      </div>
    </DashboardLayout>
  );
};

export default CreateStrategyPage;
