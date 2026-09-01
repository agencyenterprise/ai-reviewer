import { Issue, SeverityEnum, WorkflowRunType } from './generated-api';
import { getMaxSeverity } from './severity';
import { isIssueResolved } from './stores/document-explorer-store';

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
