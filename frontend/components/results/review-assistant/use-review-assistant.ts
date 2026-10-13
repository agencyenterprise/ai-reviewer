'use client';

import { getErrorMessage } from '@/lib/api-error';
import {
  cancelWorkflowRunEndpointApiWorkflowRunsWorkflowRunIdCancelPost,
  listReviewAssistantRequestsEndpointApiProjectProjectIdReviewAssistantRequestsGet,
  ReviewAssistantOutput,
  startReviewAssistantRequestEndpointApiProjectProjectIdReviewAssistantRequestsPost,
} from '@/lib/generated-api';
import { projectQueryKeys } from '@/lib/hooks/use-project-data';
import { isWorkflowProcessing } from '@/lib/workflow-state';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

/** Polled while a request is queued or running, so its status and results arrive on their own. */
const ACTIVE_POLL_MS = 4000;

/** The project's Review Assistant requests, newest first, across every revision. */
export function useReviewAssistantRequests(projectId: string, { enabled = true }: { enabled?: boolean } = {}) {
  return useQuery({
    enabled,
    queryKey: projectQueryKeys.reviewAssistantRequests(projectId),
    queryFn: () =>
      listReviewAssistantRequestsEndpointApiProjectProjectIdReviewAssistantRequestsGet({
        path: { project_id: projectId },
      }),
    refetchInterval: (query) =>
      (query.state.data ?? []).some((request) => isWorkflowProcessing(request)) ? ACTIVE_POLL_MS : false,
  });
}

export interface StartRequestArgs {
  outputs: ReviewAssistantOutput[];
  fileIds: string[];
}

export function useStartReviewAssistantRequest(projectId: string, onStarted: (runId: string) => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ outputs, fileIds }: StartRequestArgs) =>
      startReviewAssistantRequestEndpointApiProjectProjectIdReviewAssistantRequestsPost({
        path: { project_id: projectId },
        body: { outputs, file_ids: fileIds },
      }),
    onSuccess: async (response) => {
      await queryClient.invalidateQueries({ queryKey: projectQueryKeys.all(projectId) });
      onStarted(response.workflow_run_id);
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Failed to start the Review Assistant')),
  });
}

export function useCancelReviewAssistantRequest(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (runId: string) =>
      cancelWorkflowRunEndpointApiWorkflowRunsWorkflowRunIdCancelPost({ path: { workflow_run_id: runId } }),
    onSuccess: () => {
      toast.success('Request cancelled');
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.all(projectId) });
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Failed to cancel the request')),
  });
}
