import { WorkflowRunType } from '@/lib/generated-api';

/**
 * Runs that belong to a tab of their own rather than to Assessments. A Review
 * Assistant request reads the documents it was handed, not the draft, so it
 * is listed and started only from the Review Assistant tab.
 */
export function isAssessmentRun(type: WorkflowRunType): boolean {
  return type !== WorkflowRunType.ReviewAssistant;
}
