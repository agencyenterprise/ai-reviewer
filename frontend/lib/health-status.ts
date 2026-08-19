import { Issue, SeverityEnum, WorkflowRunDetail, WorkflowRunStatus, WorkflowRunType } from './generated-api';
import { getMaxSeverity } from './severity';
import { isIssueResolved } from './stores/document-explorer-store';
import { getDisplayStatus } from './workflow-state';

/**
 * Health status for a workflow widget
 */
export type HealthStatus = 'healthy' | 'issues' | 'processing' | 'error';

/**
 * Aggregated health data for a workflow type
 */
export interface WorkflowHealthData {
  type: WorkflowRunType;
  status: HealthStatus;
  issueCount: number;
  highSeverityCount: number;
  mediumSeverityCount: number;
  lowSeverityCount: number;
  workflowRun: WorkflowRunDetail;
}

/**
 * The reported issues of one workflow type, for at-a-glance display.
 */
export interface ReportedIssuesSummary {
  /** Every reported issue, across severities. */
  total: number;
  /** Per severity; `none` is always 0, since passing checks are not reported. */
  counts: Record<SeverityEnum, number>;
  /** Undefined when nothing was reported. Drives the badge's icon and colour. */
  maxSeverity?: SeverityEnum;
}

/**
 * Summarise the issues one workflow type reported.
 *
 * The single counting rule for the app: passing checks (severity `none`) and
 * resolved issues are excluded, matching the document explorer's defaults, so
 * every count the user sees agrees with the list they land on.
 */
export function summarizeReportedIssues(issues: Issue[], workflowType: WorkflowRunType): ReportedIssuesSummary {
  const reported = issues.filter(
    (issue) => issue.workflow_type === workflowType && issue.severity !== SeverityEnum.None && !isIssueResolved(issue),
  );

  const counts: Record<SeverityEnum, number> = {
    [SeverityEnum.None]: 0,
    [SeverityEnum.Low]: 0,
    [SeverityEnum.Medium]: 0,
    [SeverityEnum.High]: 0,
  };
  reported.forEach((issue) => {
    counts[issue.severity] += 1;
  });

  return { total: reported.length, counts, maxSeverity: getMaxSeverity(reported) };
}

/**
 * Whether a workflow's findings warrant attention. Only Medium and High
 * severity issues affect health status.
 */
function hasHealthAffectingIssues(summary: ReportedIssuesSummary): boolean {
  return summary.counts[SeverityEnum.High] > 0 || summary.counts[SeverityEnum.Medium] > 0;
}

/**
 * Determines the health status for a workflow from its run status and the
 * issues it reported.
 */
function determineHealthStatus(workflowRun: WorkflowRunDetail, summary: ReportedIssuesSummary): HealthStatus {
  const displayStatus = getDisplayStatus(workflowRun);

  if (displayStatus === 'failed') return 'error';

  if (workflowRun.run.status === WorkflowRunStatus.Pending || workflowRun.run.status === WorkflowRunStatus.Running) {
    return 'processing';
  }

  return hasHealthAffectingIssues(summary) ? 'issues' : 'healthy';
}

/**
 * Aggregates health data for all workflow runs.
 *
 * Counts come from `summarizeReportedIssues`, so the health monitor, the
 * assessment badges and the document explorer all agree on what an issue is:
 * a resolved finding stops counting everywhere at once.
 */
export function aggregateWorkflowHealth(workflowRuns: WorkflowRunDetail[], issues: Issue[]): WorkflowHealthData[] {
  return workflowRuns.map((workflowRun) => {
    const summary = summarizeReportedIssues(issues, workflowRun.run.type);

    return {
      type: workflowRun.run.type,
      status: determineHealthStatus(workflowRun, summary),
      issueCount: summary.total,
      highSeverityCount: summary.counts[SeverityEnum.High],
      mediumSeverityCount: summary.counts[SeverityEnum.Medium],
      lowSeverityCount: summary.counts[SeverityEnum.Low],
      workflowRun,
    };
  });
}

/**
 * Calculates overall project health from individual workflow health data
 */
export function calculateOverallHealth(healthData: WorkflowHealthData[]): HealthStatus {
  if (healthData.length === 0) return 'healthy';

  // If any workflow has an error, overall is error
  if (healthData.some((h) => h.status === 'error')) return 'error';

  // If any workflow has issues, overall has issues
  if (healthData.some((h) => h.status === 'issues')) return 'issues';

  // If any workflow is processing, overall is processing
  if (healthData.some((h) => h.status === 'processing')) return 'processing';

  return 'healthy';
}

/**
 * Configuration for health status display
 */
export const healthStatusConfig: Record<
  HealthStatus,
  {
    description: string;
    colorClass: string;
    borderClass: string;
  }
> = {
  healthy: {
    description: 'No significant issues found',
    colorClass: 'text-green-600',
    borderClass: 'border-green-200',
  },
  issues: {
    description: 'Review recommended',
    colorClass: 'text-amber-600',
    borderClass: 'border-amber-200',
  },
  processing: {
    description: 'Analysis in progress',
    colorClass: 'text-blue-600',
    borderClass: 'border-blue-200',
  },
  error: {
    description: 'Analysis failed',
    colorClass: 'text-red-600',
    borderClass: 'border-red-200',
  },
};
