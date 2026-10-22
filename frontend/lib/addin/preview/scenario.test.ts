import { describe, expect, it } from 'vitest';
import { DEFAULT_SCENARIO, scenarioFrom, scenarioQuery } from './scenario';

describe('preview scenarios', () => {
  it('reads the defaults from an empty query, and writes none of them back', () => {
    expect(scenarioFrom(new URLSearchParams())).toEqual(DEFAULT_SCENARIO);
    expect(scenarioQuery(DEFAULT_SCENARIO)).toBe('');
  });

  it('round-trips every setting through the query string', () => {
    const scenario = { teams: false, waiting: 'both', chat: 'card', key: false, width: 400 } as const;
    expect(scenarioFrom(new URLSearchParams(scenarioQuery(scenario)))).toEqual(scenario);
  });

  it('ignores values it does not know rather than breaking the page', () => {
    const scenario = scenarioFrom(new URLSearchParams('waiting=later&chat=x&width=9000'));
    expect(scenario).toEqual(DEFAULT_SCENARIO);
  });
});
