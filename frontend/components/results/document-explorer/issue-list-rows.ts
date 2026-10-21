import { Issue, SeverityEnum } from '@/lib/generated-api';
import { SEVERITIES_WORST_FIRST } from '@/lib/severity';

export type IssueListRow = { kind: 'header'; severity: SeverityEnum; count: number } | { kind: 'issue'; issue: Issue };

/**
 * The issue queue's rows, in the order the issues arrive. Grouped, each
 * severity gets a header over its issues. Ungrouped, the reported issues run as
 * one list without headers; passing checks keep theirs, since "passing" is not
 * a priority.
 */
export function issueListRows(issues: Issue[], groupBySeverity: boolean): IssueListRow[] {
  const out: IssueListRow[] = [];
  if (!groupBySeverity) {
    for (const issue of issues) {
      if (issue.severity !== SeverityEnum.None) out.push({ kind: 'issue', issue });
    }
  }
  const groups = groupBySeverity ? SEVERITIES_WORST_FIRST : [SeverityEnum.None];
  for (const severity of groups) {
    const group = issues.filter((issue) => issue.severity === severity);
    if (group.length === 0) continue;
    out.push({ kind: 'header', severity, count: group.length });
    for (const issue of group) out.push({ kind: 'issue', issue });
  }
  return out;
}
