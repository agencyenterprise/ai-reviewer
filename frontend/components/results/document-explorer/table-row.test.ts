import { describe, expect, it } from 'vitest';
import { lineDataAttributes } from './table-row';

describe('lineDataAttributes', () => {
  it('stamps a row with its source lines', () => {
    const position = { start: { line: 6, column: 1 }, end: { line: 6, column: 26 } };

    expect(lineDataAttributes(position)).toEqual({ 'data-line-start': 6, 'data-line-end': 6 });
  });

  it('stamps nothing for a row without a source position', () => {
    expect(lineDataAttributes(undefined)).toEqual({});
  });
});
