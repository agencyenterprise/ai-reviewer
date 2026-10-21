'use client';

import { WorkflowRunType } from '@/lib/generated-api';
import { useMutationState } from '@tanstack/react-query';

/** The key of a project's "start these assessments" mutations. */
export function startAssessmentsKey(projectId: string) {
  return ['start-assessments', projectId] as const;
}

/**
 * The assessments every start still in flight asked for, not just the latest
 * one: a mutation's own `variables` only hold its last call, and an earlier
 * batch the overview has not caught up with yet would become selectable again.
 * Keyed by project, so every Run assessments button on the page sees the same
 * starts.
 */
export function useStartingWorkflowTypes(projectId: string): WorkflowRunType[] {
  const batches = useMutationState({
    filters: { mutationKey: startAssessmentsKey(projectId), status: 'pending' },
    select: (mutation) =>
      (mutation.state.variables as { workflowTypes?: WorkflowRunType[] } | undefined)?.workflowTypes,
  });
  return batches.flatMap((types) => types ?? []);
}
