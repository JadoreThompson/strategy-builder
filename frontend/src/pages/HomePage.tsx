import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, BrainCircuit, Rocket, Scale } from "lucide-react";
import type { FC } from "react";
import { Link } from "react-router";

const HomePage: FC = () => {
  return (
    <div className="bg-background text-foreground min-h-screen font-sans">
      {/* Header */}
      <header className="border-border/40 bg-background/95 supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 w-full border-b backdrop-blur">
        <div className="container mx-auto flex h-14 max-w-screen-2xl items-center justify-between px-4 md:px-6">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold">
            <Scale className="text-primary h-6 w-6" />
            <span>StratBuilder</span>
          </Link>
          <div className="flex items-center gap-2">
            <Button variant="ghost" asChild>
              <Link to="/login">Login</Link>
            </Button>
            <Button asChild>
              <Link to="/register">Sign Up</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="relative px-4 py-24 text-center md:py-32 lg:py-40">
          <div className="absolute inset-0 -z-10 h-full w-full bg-white bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px]"></div>
          <div className="container mx-auto max-w-4xl">
            <h1 className="text-primary text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
              From Idea to Live Deployment, Seamlessly.
            </h1>
            <p className="text-muted-foreground mt-6 text-lg md:text-xl">
              StratBuilder provides a complete zero-code toolkit to create,
              backtest, and deploy optimized trading strategies. Turn your
              market insights into automated success.
            </p>
            <div className="mt-8 flex justify-center gap-4">
              <Button size="lg" asChild>
                <Link to="/register">Get Started For Free</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="bg-secondary py-16 sm:py-24">
          <div className="container mx-auto max-w-6xl px-4">
            <div className="mb-12 text-center">
              <h2 className="text-primary text-3xl font-bold tracking-tight sm:text-4xl">
                An Institutional-Grade Toolkit for Every Trader
              </h2>
              <p className="text-muted-foreground mt-4 text-lg">
                Everything you need to gain a competitive edge in the markets.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
              <Card className="text-center">
                <CardHeader>
                  <div className="bg-primary text-primary-foreground mx-auto flex h-12 w-12 items-center justify-center rounded-full">
                    <BrainCircuit className="h-6 w-6" />
                  </div>
                  <CardTitle className="mt-4 text-xl font-semibold">
                    Intuitive Strategy Creation
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-muted-foreground">
                  Describe your trading logic using natural language. Our
                  advanced engine translates your ideas into a robust strategy
                  without a single line of code.
                </CardContent>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="bg-primary text-primary-foreground mx-auto flex h-12 w-12 items-center justify-center rounded-full">
                    <BarChart className="h-6 w-6" />
                  </div>
                  <CardTitle className="mt-4 text-xl font-semibold">
                    Powerful Backtesting
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-muted-foreground">
                  Validate your strategies against historical data with instant,
                  in-depth performance analytics. Visualize PnL, win rates, and
                  drawdowns to refine your approach.
                </CardContent>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="bg-primary text-primary-foreground mx-auto flex h-12 w-12 items-center justify-center rounded-full">
                    <Rocket className="h-6 w-6" />
                  </div>
                  <CardTitle className="mt-4 text-xl font-semibold">
                    One-Click Deployment
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-muted-foreground">
                  Connect your brokerage account and deploy your automated
                  strategy to the live market effortlessly. Monitor and manage
                  all active deployments from a unified dashboard.
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Showcase Section */}
        <section className="py-16 sm:py-24">
          <div className="container mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-4 md:grid-cols-2">
            <div>
              <span className="text-primary text-sm font-semibold uppercase">
                Visualize Performance
              </span>
              <h3 className="mt-2 text-3xl font-bold tracking-tight">
                Data-Driven Decisions Made Simple
              </h3>
              <p className="text-muted-foreground mt-4 text-lg">
                Our dashboard provides a clean, elegant interface that surfaces
                the most critical metrics. Quickly compare versions, analyze
                performance curves, and identify your most promising strategies.
              </p>
            </div>
            <div className="flex items-center justify-center">
              {/* This is a simplified, static representation of the StrategyVersionCard */}
              <div className="grid h-full w-full max-w-lg cursor-pointer grid-cols-2 gap-2 rounded-xl border-2 border-gray-200 p-4 shadow-2xl shadow-gray-200">
                <div className="flex flex-col gap-8 py-3">
                  <div className="flex items-center gap-3">
                    <h4 className="text-lg font-medium">Momentum Scalper</h4>
                    <span className="h-fit w-fit rounded bg-green-200/50 p-1 text-xs text-green-600">
                      Completed
                    </span>
                  </div>
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-row justify-between gap-2">
                      <span className="text-sm">Pnl</span>
                      <span className="text-md font-semibold text-green-600">
                        $2,480.50
                      </span>
                    </div>
                    <div className="flex flex-row justify-between gap-2">
                      <span className="text-sm">Win Rate</span>
                      <span className="text-md font-semibold">68%</span>
                    </div>
                    <div className="flex flex-row justify-between gap-2">
                      <span className="text-sm">Max Drawdown</span>
                      <span className="text-md font-semibold">4.2%</span>
                    </div>
                  </div>
                </div>
                {/* Simplified Chart Visual */}
                <div className="h-full w-full">
                  <svg
                    width="100%"
                    height="100%"
                    viewBox="0 0 100 50"
                    preserveAspectRatio="none"
                  >
                    <path
                      d="M 0 40 C 20 10, 40 10, 60 30 S 80 45, 100 20"
                      stroke="#5a76b9"
                      fill="transparent"
                      strokeWidth="2"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="bg-secondary py-16 sm:py-24">
          <div className="container mx-auto max-w-4xl px-4 text-center">
            <h2 className="text-primary text-3xl font-bold tracking-tight sm:text-4xl">
              Ready to Automate Your Edge?
            </h2>
            <p className="text-muted-foreground mt-4 text-lg">
              Create an account and start building your first strategy in
              minutes. No credit card required.
            </p>
            <div className="mt-8">
              <Button size="lg" asChild>
                <Link to="/register">Sign Up Now</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t">
        <div className="container mx-auto flex flex-col items-center justify-between gap-4 px-4 py-6 md:flex-row">
          <div className="flex items-center gap-2 font-semibold">
            <Scale className="text-primary h-5 w-5" />
            <span>StratBuilder</span>
          </div>
          <p className="text-muted-foreground text-sm">
            © {new Date().getFullYear()} StratBuilder. All Rights Reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
