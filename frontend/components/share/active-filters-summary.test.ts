import { describe, expect, it } from 'vitest';
import { exportCountsStatus, narrowsTheExport } from './active-filters-summary';
import { SeverityEnum, WorkflowRunType } from '@/lib/generated-api';

const NONE = { severity: [], workflowType: [], showPassing: false };
const ALL_SEVERITIES = [SeverityEnum.High, SeverityEnum.Medium, SeverityEnum.Low];

describe('narrowsTheExport', () => {
  it('is false when nothing narrows the export', () => {
    expect(narrowsTheExport(NONE)).toBe(false);
    // Every severity selected is the same scope as selecting none.
    expect(narrowsTheExport({ ...NONE, severity: ALL_SEVERITIES })).toBe(false);
  });

  it('is true for a partial severity or an assessment filter', () => {
    expect(narrowsTheExport({ ...NONE, severity: [SeverityEnum.High] })).toBe(true);
    expect(narrowsTheExport({ ...NONE, workflowType: [WorkflowRunType.FiguresTablesCheck] })).toBe(true);
  });

  it('ignores the passing toggle, which only widens the export', () => {
    expect(narrowsTheExport({ ...NONE, showPassing: true })).toBe(false);
  });
});

describe('exportCountsStatus', () => {
  it('is counting, not zero, while the issues load', () => {
    expect(exportCountsStatus(null, false)).toBe('counting');
  });

  it('is failed when the issues could not be loaded', () => {
    expect(exportCountsStatus(null, true)).toBe('failed');
  });

  it('is known once the counts arrive, zero included', () => {
    expect(exportCountsStatus({ issues: 3, edits: 1 }, false)).toBe('known');
    expect(exportCountsStatus({ issues: 0, edits: 0 }, false)).toBe('known');
  });
});
