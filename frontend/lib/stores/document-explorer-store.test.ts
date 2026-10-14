import { SeverityEnum, WorkflowRunType, type Issue } from '@/lib/generated-api';
import { describe, expect, it } from 'vitest';
import { DEFAULT_FILTER, getFilteredIssues, getResolvedCount, getVisibleIssues } from './document-explorer-store';

function issue(
  id: string,
  lines: { start_line?: number | null; end_line?: number | null },
  overrides: Partial<Issue> = {},
): Issue {
  return {
    id,
    project_id: 'project-1',
    workflow_run_id: 'run-1',
    issue_hash: `hash-${id}`,
    title: 'A finding',
    description: 'Something to look at',
    severity: SeverityEnum.Medium,
    workflow_type: WorkflowRunType.AdvocacyToneV2,
    created_at: new Date('2026-01-01T00:00:00Z'),
    updated_at: new Date('2026-01-01T00:00:00Z'),
    edits: [],
    ...lines,
    ...overrides,
  } as Issue;
}

const ids = (issues: Issue[]) => issues.map((i) => i.id);

describe('getFilteredIssues with a selected line range', () => {
  const issues = [
    issue('before', { start_line: 1, end_line: 4 }),
    issue('touches-start', { start_line: 3, end_line: 5 }),
    issue('inside', { start_line: 6, end_line: 7 }),
    issue('touches-end', { start_line: 8, end_line: 12 }),
    issue('after', { start_line: 9, end_line: 12 }),
    issue('start-only', { start_line: 6 }),
    issue('unanchored', {}),
  ];

  it('keeps issues overlapping the range, ends inclusive, and drops issues without both lines', () => {
    expect(ids(getFilteredIssues(issues, DEFAULT_FILTER, [5, 8]))).toEqual(['touches-start', 'inside', 'touches-end']);
  });

  it('keeps every issue when no range is selected', () => {
    expect(ids(getFilteredIssues(issues, DEFAULT_FILTER, null))).toEqual(ids(issues));
  });
});

describe('getResolvedCount', () => {
  const resolved = { resolved_at: new Date('2026-01-02T00:00:00Z') };
  const issues = [
    issue('in', { start_line: 5, end_line: 6 }, resolved),
    issue('out', { start_line: 20, end_line: 21 }, resolved),
    issue('open', { start_line: 5, end_line: 6 }),
    issue('unanchored', {}, resolved),
  ];

  it('counts resolved issues inside the selected range only', () => {
    expect(getResolvedCount(issues, [1, 10])).toBe(1);
  });

  it('counts every resolved issue when no range is selected', () => {
    expect(getResolvedCount(issues, null)).toBe(3);
  });
});

describe('getVisibleIssues', () => {
  it('orders same-severity issues by start line, unanchored ones first', () => {
    const issues = [
      issue('late', { start_line: 30, end_line: 31 }),
      issue('start-only', { start_line: 10 }),
      issue('unanchored', {}),
      issue('early', { start_line: 2, end_line: 2 }),
    ];
    expect(ids(getVisibleIssues(issues, DEFAULT_FILTER))).toEqual(['unanchored', 'early', 'start-only', 'late']);
  });
});
