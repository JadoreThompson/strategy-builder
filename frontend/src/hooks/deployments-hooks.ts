import { queryKeys } from "@/lib/query/query-keys";
import { handleApi } from "@/lib/utils/base";
import {
  createDeploymentDeploymentsPost,
  getDeploymentDeploymentsDeploymentIdGet,
  stopDeploymentDeploymentsDeploymentIdStopPost,
  type DeploymentCreate,
} from "@/openapi";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useDeploymentQuery(deploymentId: string) {
  return useQuery({
    queryKey: queryKeys.deployment(deploymentId),
    queryFn: async () =>
      handleApi(await getDeploymentDeploymentsDeploymentIdGet(deploymentId)),
    enabled: !!deploymentId,
  });
}

export function useCreateDeploymentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: DeploymentCreate) =>
      handleApi(await createDeploymentDeploymentsPost(data)),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.deploymentsByVersion(variables.version_id),
      });
    },
  });
}

export function useStopDeploymentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { deploymentId: string; versionId: string }) =>
      handleApi(
        await stopDeploymentDeploymentsDeploymentIdStopPost(
          params.deploymentId,
        ),
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.deployment(variables.deploymentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.deploymentsByVersion(variables.versionId),
      });
    },
  });
}
