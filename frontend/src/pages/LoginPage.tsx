import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useLoginMutation } from "@/hooks/auth-hooks";
import { useState, type FC } from "react";
import { Link, useNavigate } from "react-router";

const LoginPage: FC = () => {
  const navigate = useNavigate();
  const loginMutation = useLoginMutation();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    loginMutation
      .mutateAsync({ username, password })
      .then(() => navigate("/strategies"));
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Welcome Back</CardTitle>
          <CardDescription>
            Enter your credentials to access your dashboard
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                className="mb-1 block text-sm font-medium"
                htmlFor="username"
              >
                Username
              </label>
              <Input
                id="username"
                type="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="username"
                required
                disabled={loginMutation.isPending}
              />
            </div>
            <div>
              <label
                className="mb-1 block text-sm font-medium"
                htmlFor="password"
              >
                Password
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={loginMutation.isPending}
              />
            </div>
            {loginMutation.error && (
              <p className="text-sm font-medium text-red-600">
                {loginMutation.error.message}
              </p>
            )}
            <Button
              type="submit"
              className="w-full"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? "Logging in..." : "Login"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{" "}
            <Link
              to="/register"
              className="text-primary font-medium hover:underline"
            >
              Sign up
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default LoginPage;
