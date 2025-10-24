import { feedbackApi } from '@/lib/api';
import type { FeedbackRequest, FeedbackType } from '@/lib/generated-api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

/**
 * Generic feedback hook for any entity
 *
 * @example
 * // For a claim
 * const claim = useFeedback(workflowId, { chunk_index: 0, claim_index: 1 });
 *
 * // For a chunk
 * const chunk = useFeedback(workflowId, { chunk_index: 0 });
 *
 * // For workflow
 * const workflow = useFeedback(workflowId, {});
 *
 * // For a reference
 * const ref = useFeedback(workflowId, { reference_index: 2 });
 */
export function useFeedback(workflowRunId: string, entityPath: Record<string, number>) {
  const queryClient = useQueryClient();

  const queryKey = ['feedback', workflowRunId, entityPath];

  const { data: feedback, isLoading } = useQuery({
    queryKey,
    queryFn: async () => {
      try {
        return await feedbackApi.getFeedbackApiFeedbackGet({
          workflowRunId,
          entityPath: JSON.stringify(entityPath),
        });
      } catch {
        return null;
      }
    },
    enabled: !!workflowRunId,
  });

  const submitMutation = useMutation({
    mutationFn: async (request: { feedback_type: FeedbackType; feedback_text?: string | null }) => {
      const feedbackRequest: FeedbackRequest = {
        workflowRunId,
        entityPath,
        feedbackType: request.feedback_type,
        feedbackText: request.feedback_text || undefined,
      };

      return await feedbackApi.submitFeedbackApiFeedbackPost({
        feedbackRequest,
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
