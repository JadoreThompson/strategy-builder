import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  createAccountAccountsPost,
  deleteAccountAccountsAccountIdDelete,
  getAccountAccountsAccountIdGet,
  getAccountsAccountsGet,
  updateAccountAccountsAccountIdPatch,
  type AccountCreate,
  type AccountUpdate,
  type GetAccountsAccountsGetParams,
} from "@/openapi";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

export function useAccountsQuery(params?: GetAccountsAccountsGetParams) {
  return useQuery({
    queryKey: queryKeys.accounts(params),
    queryFn: async () => handleApi(await getAccountsAccountsGet(params)),
  });
}

export function useInfiniteAccountsQuery(
  params?: GetAccountsAccountsGetParams,
) {
  return useInfiniteQuery({
    queryKey: queryKeys.accounts(),
    queryFn: async ({ pageParam = 1 }) =>
      handleApi(
        await getAccountsAccountsGet({
          ...params,
          page: pageParam,
        }),
      ),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.has_next) {
        return lastPage.page + 1;
      }
      return undefined;
    },
  });
}

export function useAccountQuery(accountId: string) {
  return useQuery({
    queryKey: queryKeys.account(accountId),
    queryFn: async () =>
      handleApi(await getAccountAccountsAccountIdGet(accountId)),
    enabled: !!accountId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateAccountMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AccountCreate) =>
      handleApi(await createAccountAccountsPost(data)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts() });
    },
  });
}

export function useUpdateAccountMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { accountId: string; data: AccountUpdate }) =>
      handleApi(
        await updateAccountAccountsAccountIdPatch(
          params.accountId,
          params.data,
        ),
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts() });
      queryClient.invalidateQueries({
        queryKey: queryKeys.account(variables.accountId),
      });
    },
  });
}

export function useDeleteAccountMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (accountId: string) =>
      handleApi(await deleteAccountAccountsAccountIdDelete(accountId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts() });
    },
  });
}
