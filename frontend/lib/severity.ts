import { Issue, SeverityEnum } from './generated-api';

/** Every severity, worst first. */
export const SEVERITIES_WORST_FIRST = [
  SeverityEnum.High,
  SeverityEnum.Medium,
  SeverityEnum.Low,
  SeverityEnum.None,
] as const;

/** The severities that flag a problem, worst first: all but the passing `none`. */
export const REPORTED_SEVERITIES = [SeverityEnum.High, SeverityEnum.Medium, SeverityEnum.Low] as const;

const RANK = Object.fromEntries(
  SEVERITIES_WORST_FIRST.map((severity, i) => [severity, SEVERITIES_WORST_FIRST.length - 1 - i]),
) as Record<SeverityEnum, number>;

/** Higher is worse: `none` ranks 0 and `high` ranks 3. */
export function severityRank(severity: SeverityEnum): number {
  return RANK[severity];
}

export function sortIssueBySeverity(a: Issue, b: Issue) {
  return severityRank(b.severity) - severityRank(a.severity);
}

export function getMaxSeverity(issues: Issue[]): SeverityEnum | undefined {
  return SEVERITIES_WORST_FIRST.find((severity) => issues.some((issue) => issue.severity === severity));
}
