import { feedbackApi } from '@/lib/api';
import type { ClaimFeedbackRequest, FeedbackType } from '@/lib/generated-api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

export function useClaimFeedback(workflowRunId: string, chunkIndex: number, claimIndex: number) {
  const queryClient = useQueryClient();

  const queryKey = ['claim-feedback', workflowRunId, chunkIndex, claimIndex];

  const { data: feedback, isLoading } = useQuery({
    queryKey,
    queryFn: async () => {
      try {
        return await feedbackApi.getClaimFeedbackApiFeedbackClaimGet({
          workflowRunId,
          chunkIndex,
          claimIndex,
        });
      } catch {
        return null;
      }
    },
    enabled: !!workflowRunId,
  });

  const submitMutation = useMutation({
    mutationFn: async (request: { feedback_type: FeedbackType; feedback_text?: string | null }) => {
      const claimFeedbackRequest: ClaimFeedbackRequest = {
        workflowRunId,
        chunkIndex,
        claimIndex,
        feedbackType: request.feedback_type,
        feedbackText: request.feedback_text || undefined,
      };

      return await feedbackApi.submitClaimFeedbackApiFeedbackClaimPost({
        claimFeedbackRequest,
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(queryKey, data);
    },
  });

  return {
    feedback,
    isLoading,
    submitFeedback: submitMutation.mutate,
    isSubmitting: submitMutation.isPending,
  };
}
