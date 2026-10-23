import { Issue, SeverityEnum, WorkflowRunType } from './generated-api';
import { getMaxSeverity, REPORTED_SEVERITIES } from './severity';
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

/**
 * What an assessment's count badge leads with. Grouped, the size of the worst
 * tier, so the colour and the number describe the same thing. Ungrouped, every
 * reported issue counts the same, as medium.
 */
export function badgeHeadline(
  summary: ReportedIssuesSummary,
  groupBySeverity: boolean,
): { severity: SeverityEnum; count: number } {
  if (!summary.maxSeverity) return { severity: SeverityEnum.None, count: 0 };
  if (!groupBySeverity) return { severity: SeverityEnum.Medium, count: summary.total };
  return { severity: summary.maxSeverity, count: summary.counts[summary.maxSeverity] };
}

/**
 * The per-severity lines of an assessment's tooltip, most severe first. Empty
 * when the project doesn't group by severity, so no High or Low label shows
 * where every issue otherwise reads as medium.
 */
export function badgeBreakdown(
  summary: ReportedIssuesSummary,
  groupBySeverity: boolean,
): { severity: SeverityEnum; count: number }[] {
  if (!groupBySeverity) return [];
  return REPORTED_SEVERITIES.filter((severity) => summary.counts[severity] > 0).map((severity) => ({
    severity,
    count: summary.counts[severity],
  }));
}
