import type {
  GetAccountsAccountsGetParams,
  GetStrategiesStrategiesGetParams,
} from "@/openapi";

export const queryKeys = {
  accounts: (params?: GetAccountsAccountsGetParams) =>
    ["accounts", params] as const,
  account: (params: string) => ["account", params] as const,
  backtests: () => ["backtests"] as const,
  deployments: () => ["deployments"] as const,
  positions: () => ["positions"] as const,
  strategies: (params?: GetStrategiesStrategiesGetParams) =>
    ["strategies", params] as const,
  versions: () => ["versions"] as const,
};
