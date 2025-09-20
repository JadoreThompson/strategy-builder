import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  getWsTokenAuthWsTokenGet,
  loginAuthLoginPost,
  registerAuthRegisterPost,
  type UserCreate,
  type UserLogin,
} from "@/openapi";
import { useMutation, useQuery } from "@tanstack/react-query";

export function useRegisterMutation() {
  return useMutation({
    mutationFn: async (data: UserCreate) =>
      handleApi(await registerAuthRegisterPost(data)),
  });
}

export function useLoginMutation() {
  return useMutation({
    mutationFn: async (data: UserLogin) =>
      handleApi(await loginAuthLoginPost(data)),
  });
}

export function useWsTokenQuery() {
  return useQuery({
    queryKey: queryKeys.wsToken(),
    queryFn: async () => handleApi(await getWsTokenAuthWsTokenGet()),
    staleTime: 5 * 60 * 1000,
  });
}
