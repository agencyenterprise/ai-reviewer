import { describe, expect, it } from 'vitest';

import { Issue, SeverityEnum } from './generated-api';
import { getMaxSeverity, severityRank, sortIssueBySeverity } from './severity';

const issue = (id: string, severity: SeverityEnum) => ({ id, severity }) as Issue;

describe('sortIssueBySeverity', () => {
  it('puts the worst issues first and keeps ties in their original order', () => {
    const issues = [
      issue('none', SeverityEnum.None),
      issue('low', SeverityEnum.Low),
      issue('high-1', SeverityEnum.High),
      issue('medium', SeverityEnum.Medium),
      issue('high-2', SeverityEnum.High),
    ];

    expect(issues.sort(sortIssueBySeverity).map((i) => i.id)).toEqual(['high-1', 'high-2', 'medium', 'low', 'none']);
  });
});

describe('getMaxSeverity', () => {
  it('returns the worst severity present', () => {
    expect(getMaxSeverity([issue('a', SeverityEnum.Low), issue('b', SeverityEnum.Medium)])).toBe(SeverityEnum.Medium);
    expect(getMaxSeverity([issue('a', SeverityEnum.None), issue('b', SeverityEnum.High)])).toBe(SeverityEnum.High);
  });

  it('returns none when only passing checks are present', () => {
    expect(getMaxSeverity([issue('a', SeverityEnum.None)])).toBe(SeverityEnum.None);
  });

  it('returns undefined for no issues', () => {
    expect(getMaxSeverity([])).toBeUndefined();
  });
});

describe('severityRank', () => {
  it('ranks worse severities higher', () => {
    expect([SeverityEnum.None, SeverityEnum.Low, SeverityEnum.Medium, SeverityEnum.High].map(severityRank)).toEqual([
      0, 1, 2, 3,
    ]);
  });
});
