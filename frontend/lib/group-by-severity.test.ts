import { describe, expect, it } from 'vitest';

import { issueListRows } from '@/components/results/document-explorer/issue-list-rows';
import { Issue, SeverityEnum } from './generated-api';
import { badgeHeadline, ReportedIssuesSummary } from './health-status';
import { SEVERITY, severityStyle } from './severity-style';
import { DEFAULT_FILTER, withSeverityGrouping } from './stores/document-explorer-store';

const issue = (id: string, severity: SeverityEnum) => ({ id, severity }) as Issue;

const rowKeys = (issues: Issue[], grouped: boolean) =>
  issueListRows(issues, grouped).map((row) => (row.kind === 'header' ? `header:${row.severity}` : row.issue.id));

describe('issueListRows', () => {
  const issues = [
    issue('high', SeverityEnum.High),
    issue('medium', SeverityEnum.Medium),
    issue('low', SeverityEnum.Low),
    issue('passing', SeverityEnum.None),
  ];

  it('puts each severity under its own header when grouped', () => {
    expect(rowKeys(issues, true)).toEqual([
      'header:high',
      'high',
      'header:medium',
      'medium',
      'header:low',
      'low',
      'header:none',
      'passing',
    ]);
  });

  it('lists reported issues without headers, in the order given, when ungrouped', () => {
    expect(rowKeys(issues, false)).toEqual(['high', 'medium', 'low', 'header:none', 'passing']);
  });
});

describe('severityStyle', () => {
  it('shows every reported issue as an unlabelled medium when ungrouped', () => {
    for (const severity of [SeverityEnum.High, SeverityEnum.Low]) {
      expect(severityStyle(severity, false)).toEqual({ ...SEVERITY[SeverityEnum.Medium], label: '' });
    }
  });

  it('keeps passing checks and grouped issues as they are', () => {
    expect(severityStyle(SeverityEnum.None, false)).toBe(SEVERITY[SeverityEnum.None]);
    expect(severityStyle(SeverityEnum.High, true)).toBe(SEVERITY[SeverityEnum.High]);
  });
});

describe('withSeverityGrouping', () => {
  const filter = { ...DEFAULT_FILTER, severity: [SeverityEnum.High], showPassing: true };

  it('drops a severity filter the ungrouped project has no control for', () => {
    expect(withSeverityGrouping(filter, false)).toEqual({ ...filter, severity: [] });
  });

  it('leaves the filter alone when grouped', () => {
    expect(withSeverityGrouping(filter, true)).toBe(filter);
  });
});

describe('badgeHeadline', () => {
  const summary: ReportedIssuesSummary = {
    total: 112,
    counts: {
      [SeverityEnum.None]: 0,
      [SeverityEnum.Low]: 107,
      [SeverityEnum.Medium]: 5,
      [SeverityEnum.High]: 0,
    },
    maxSeverity: SeverityEnum.Medium,
  };

  it('leads with the worst tier when grouped', () => {
    expect(badgeHeadline(summary, true)).toEqual({ severity: SeverityEnum.Medium, count: 5 });
  });

  it('leads with every reported issue, as medium, when ungrouped', () => {
    expect(badgeHeadline({ ...summary, maxSeverity: SeverityEnum.Low }, false)).toEqual({
      severity: SeverityEnum.Medium,
      count: 112,
    });
  });

  it('shows nothing to fix when nothing was reported', () => {
    const empty = { ...summary, total: 0, maxSeverity: undefined };
    expect(badgeHeadline(empty, false)).toEqual({ severity: SeverityEnum.None, count: 0 });
  });
});
