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
import { useRegisterMutation } from "@/hooks/auth-hooks";
import { useState, type FC } from "react";
import { Link, useNavigate } from "react-router";

const RegisterPage: FC = () => {
  const navigate = useNavigate();
  const registerMutation = useRegisterMutation();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    registerMutation
      .mutateAsync({ username, password })
      .then(() => navigate("/strategies"));
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">
            Create an Account
          </CardTitle>
          <CardDescription>
            Enter your details below to get started
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
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="yourusername"
                required
                disabled={registerMutation.isPending}
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
                disabled={registerMutation.isPending}
              />
            </div>
            <div>
              <label
                className="mb-1 block text-sm font-medium"
                htmlFor="confirm-password"
              >
                Confirm Password
              </label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={registerMutation.isPending}
              />
            </div>
            {registerMutation.error && (
              <p className="text-sm font-medium text-red-600">
                {registerMutation.error.message}
              </p>
            )}
            <Button
              type="submit"
              className="w-full"
              disabled={registerMutation.isPending}
            >
              {registerMutation.isPending ? "Creating Account..." : "Register"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-gray-600">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-primary font-medium hover:underline"
            >
              Log in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default RegisterPage;
