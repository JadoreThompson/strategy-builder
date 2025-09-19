import type {
  GetAccountsAccountsGetParams,
  GetStrategiesStrategiesGetParams,
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
  deploymentsByVersion: (versionId: string) =>
    ["deployments", "by-version", versionId] as const,

  // Strategies
  strategies: (params?: GetStrategiesStrategiesGetParams) =>
    ["strategies", params] as const,

  // Strategy Versions
  strategyVersions: (params: { strategyId: string } & object) =>
    ["strategies", params.strategyId, "versions", params] as const,
  strategyVersion: (versionId: string) =>
    ["strategies", "versions", versionId] as const,
  strategyVersionBacktests: (versionId: string) =>
    ["strategies", "versions", versionId, "backtests"] as const,
  strategyVersionPositions: (versionId: string) =>
    ["strategies", "versions", versionId, "positions"] as const,
};
