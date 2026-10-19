import { describe, expect, it } from 'vitest';
import { checkMessage } from './checks';

describe('checkMessage', () => {
  it('names the check for the reader and the skill for the agent', () => {
    expect(checkMessage({ name: 'Abbreviation Scan', skill: 'abbreviation-scan' })).toBe(
      'Run the Abbreviation Scan check on this document (the "abbreviation-scan" skill).',
    );
  });
});
