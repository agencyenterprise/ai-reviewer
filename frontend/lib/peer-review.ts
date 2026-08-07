import { WorkflowRunType } from '@/lib/generated-api';

/**
 * The workflows owned by the Peer Review tab, in the order of the cycle.
 *
 * They are started only from that tab, so the Analyses picker filters them out.
 * Keeping the list here means the tab and the exclusion cannot drift apart.
 */
export const PEER_REVIEW_WORKFLOW_TYPES: readonly WorkflowRunType[] = [
  WorkflowRunType.RevisionPlanningSummary,
  WorkflowRunType.ReviewerResponseMemos,
  WorkflowRunType.ReviewerCoverageReport,
] as const;

export function isPeerReviewWorkflowType(type: WorkflowRunType): boolean {
  return PEER_REVIEW_WORKFLOW_TYPES.includes(type);
}
