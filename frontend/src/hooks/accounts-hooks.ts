import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  getAccountAccountsAccountIdGet,
  getAccountsAccountsGet,
  type GetAccountsAccountsGetParams,
} from "@/openapi";
import { useQuery } from "@tanstack/react-query";

export function useAccountsQuery(params?: GetAccountsAccountsGetParams) {
  return useQuery({
    queryKey: queryKeys.accounts(params),
    queryFn: async () => handleApi(await getAccountsAccountsGet(params)),
  });
}

export function useAccountQuery(params: string) {
  return useQuery({
    queryKey: queryKeys.account(params),
    queryFn: async () =>
      handleApi(await getAccountAccountsAccountIdGet(params)),
    enabled: !!params,
    staleTime: 5 * 60 * 1000,
  });
}
