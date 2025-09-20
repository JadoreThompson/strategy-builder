import type {
  GetAccountsAccountsGetParams,
  GetStrategiesStrategiesGetParams,
  GetStrategyVersionsStrategiesStrategyIdVersionsGetParams
} from "@/openapi";

export const queryKeys = {
  // Accounts
  accounts: (params?: GetAccountsAccountsGetParams) =>
    ["accounts", params] as const,
  account: (accountId: string) => ["accounts", accountId] as const,

  // Auth
  wsToken: () => ["auth", "ws-token"] as const,

  // Backtests
  backtestResult: (backtestId: string) =>
    ["backtests", backtestId, "result"] as const,
  backtestPositionsChart: (backtestId: string) =>
    ["backtests", backtestId, "positions-chart"] as const,

  // Deployments
  deployment: (deploymentId: string) => ["deployments", deploymentId] as const,

  // Strategies
  strategies: (params?: GetStrategiesStrategiesGetParams) =>
    ["strategies", params] as const,

  // Strategy Versions
  strategyVersions: (
    params: {
      strategyId: string;
    } & GetStrategyVersionsStrategiesStrategyIdVersionsGetParams,
  ) => ["strategies-all-versions", params.strategyId, params] as const,
  strategyVersion: (versionId: string) =>
    ["strategies-versions-direct", versionId] as const,
  strategyVersionBacktests: (versionId: string) =>
    ["strategies-versions-backtests", versionId] as const,
  strategyVersionDeployments: (versionId: string) =>
    ["strategies-versions-deployments", versionId] as const,
  strategyVersionPositions: (versionId: string) =>
    ["strategies-versions-positions", versionId] as const,
};
