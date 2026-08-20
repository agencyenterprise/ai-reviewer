import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { getRecentSelectionApiWorkflowTypesRecentSelectionGet, WorkflowRunType } from '../generated-api';

/**
 * The assessments the user ran on their most recent project, used to seed the
 * new-project wizard's pre-selection.
 *
 * Fresh on every visit to the wizard, stable within a single pass through it:
 * `refetchOnMount: 'always'` re-reads it each time `WizardProvider` mounts (the
 * /new page owns the provider), while `staleTime: Infinity` stops anything else
 * from refetching underneath a user who is part-way through deciding.
 *
 * An empty `recentTypes` covers both "no history" and "the request failed";
 * callers fall back to their own default in either case.
 */
export function useRecentWorkflowSelection() {
  const query = useQuery({
    queryKey: ['recent-workflow-selection'],
    staleTime: Infinity,
    refetchOnMount: 'always',
    retry: false,
    queryFn: () => getRecentSelectionApiWorkflowTypesRecentSelectionGet(),
  });

  const recentTypes: WorkflowRunType[] = useMemo(() => query.data?.workflow_types ?? [], [query.data]);

  // `isFetching` rather than `isPending`: on a revisit the previous answer is
  // still cached, so `isPending` is already false while the refetch is in
  // flight, and the caller would seed the picker from the *previous* project.
  return { recentTypes, isPending: query.isFetching };
}
