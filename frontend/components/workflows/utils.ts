import { WorkflowRunType, WorkflowTypeDescription } from '@/lib/generated-api';

/**
 * Checks if any of the selected workflow types require web search.
 */
export function hasWebSearchRequirement(
  selectedTypes: WorkflowRunType[],
  workflowTypes?: WorkflowTypeDescription[],
): boolean {
  return selectedTypes.some((type) => workflowTypes?.find((wt) => wt.type === type)?.needs_web_search);
}

/**
 * Workflow types that require a publication date to be specified.
 */
const WORKFLOWS_REQUIRING_PUBLICATION_DATE: WorkflowRunType[] = [
  WorkflowRunType.LiteratureReview,
  WorkflowRunType.LiveReports,
];

/**
 * Checks if any of the selected workflow types require a publication date.
 */
export function hasPublicationDateRequirement(selectedTypes: WorkflowRunType[]): boolean {
  return selectedTypes.some((type) => WORKFLOWS_REQUIRING_PUBLICATION_DATE.includes(type));
}

/**
 * Workflow types that require supporting documents.
 */
export const WORKFLOWS_REQUIRING_SUPPORTING_DOCUMENTS: WorkflowRunType[] = [
  WorkflowRunType.ClaimReferenceValidation,
  WorkflowRunType.ClaimReferenceValidationV2,
  WorkflowRunType.CitationSuggester,
];

/**
 * Checks if any of the selected workflow types require supporting documents.
 */
export function hasSupportingDocumentsRequirement(selectedTypes: WorkflowRunType[]): boolean {
  return selectedTypes.some((type) => WORKFLOWS_REQUIRING_SUPPORTING_DOCUMENTS.includes(type));
}

/**
 * Formats an estimated duration (in seconds) into a short, human-friendly
 * ballpark label like "~1 min", "~3 min", or "~1.5 hr". Returns null when there
 * is no estimate to show, so callers can simply skip rendering.
 *
 * Sub-minute durations are floored to "~1 min" — showing seconds is noise at
 * this granularity.
 */
export function formatEstimatedDuration(seconds: number | null | undefined): string | null {
  if (seconds == null || !Number.isFinite(seconds) || seconds <= 0) {
    return null;
  }
  const minutes = seconds / 60;
  if (minutes < 60) {
    return `~${Math.max(1, Math.round(minutes))} min`;
  }
  const hours = minutes / 60;
  // One decimal below 10 hours (e.g. "~1.5 hr"), whole numbers above.
  const rounded = hours < 10 ? Math.round(hours * 10) / 10 : Math.round(hours);
  return `~${rounded} hr`;
}
