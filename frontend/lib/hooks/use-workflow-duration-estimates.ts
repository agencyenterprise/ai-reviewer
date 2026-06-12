import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { getDurationEstimatesApiWorkflowTypesDurationEstimatesGet, WorkflowRunType } from '../generated-api';

/**
 * Fetches the empirical "how long will this take" estimate for every workflow
 * type. Estimates are derived from past runs and change slowly, so they are
 * cached aggressively on the client. Disabled until a projectId is available.
 */
export function useWorkflowDurationEstimates(projectId: string | undefined) {
  const query = useQuery({
    queryKey: ['workflow-duration-estimates', projectId],
    enabled: !!projectId,
    staleTime: 1000 * 60 * 10, // 10 minutes — estimates drift slowly
    queryFn: async () => {
      return await getDurationEstimatesApiWorkflowTypesDurationEstimatesGet({
        query: { project_id: projectId! },
      });
    },
  });

  const estimatesByType = useMemo(() => {
    const map = new Map<WorkflowRunType, number | null>();
    for (const estimate of query.data?.estimates ?? []) {
      map.set(estimate.type, estimate.estimated_seconds);
    }
    return map;
  }, [query.data]);

  const getEstimatedSeconds = useCallback(
    (type: WorkflowRunType): number | null => estimatesByType.get(type) ?? null,
    [estimatesByType],
  );

  return { ...query, estimatesByType, getEstimatedSeconds };
}
