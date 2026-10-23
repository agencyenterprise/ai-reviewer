import { describe, expect, it } from 'vitest';

import { SeverityEnum } from './generated-api';
import { badgeBreakdown, ReportedIssuesSummary } from './health-status';

const summary: ReportedIssuesSummary = {
  total: 5,
  counts: {
    [SeverityEnum.None]: 0,
    [SeverityEnum.Low]: 3,
    [SeverityEnum.Medium]: 0,
    [SeverityEnum.High]: 2,
  },
  maxSeverity: SeverityEnum.High,
};

describe('badgeBreakdown', () => {
  it('lists the reported tiers, most severe first, when grouping by severity', () => {
    expect(badgeBreakdown(summary, true)).toEqual([
      { severity: SeverityEnum.High, count: 2 },
      { severity: SeverityEnum.Low, count: 3 },
    ]);
  });

  it('lists no tiers when the project does not group by severity', () => {
    expect(badgeBreakdown(summary, false)).toEqual([]);
  });
});
