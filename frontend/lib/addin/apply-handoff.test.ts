import { describe, expect, it } from 'vitest';
import { NOT_WRITTEN, outcomesOf, signed } from './apply-handoff';
import { NOT_FOUND, planHandoff, resultsOf } from './handoff-plan';

const PARAGRAPHS = ['Introduction', 'We recieve funding and this is the only option.', 'Funding is discussed below.'];

describe('outcomesOf', () => {
  it('reports each item by its position: written, refused by Word, or not placed', () => {
    const plan = planHandoff(
      PARAGRAPHS,
      [
        { quote: 'the only option', comment: 'Overclaims.' },
        { quote: 'vanished', comment: 'x' },
      ],
      [{ quote: 'recieve', replacement: 'receive' }],
    );

    // The comment at 0 was written; the edit at 2 was found but Word did not write it.
    const items = outcomesOf(plan, new Set([0]), NOT_WRITTEN);

    expect(items.map((item) => [item.index, item.kind, item.applied, item.reason])).toEqual([
      [0, 'comment', true, undefined],
      [1, 'comment', false, 'not_found'],
      [2, 'edit', false, 'refused'],
    ]);
    expect(items[1].detail).toBe(NOT_FOUND);
    expect(items[2].detail).toBe(NOT_WRITTEN);
  });
});

describe('signed', () => {
  it('marks a comment as Draft Detective’s once, even when the agent already did', () => {
    expect(signed('Test comment.')).toBe('Draft Detective: Test comment.');
    expect(signed('Draft Detective: Test comment.')).toBe('Draft Detective: Test comment.');
    expect(signed('draft detective — Test comment.')).toBe('Draft Detective: Test comment.');
  });
});

describe('resultsOf', () => {
  it('reports only positions, outcomes and reason codes', () => {
    expect(
      resultsOf([
        { index: 0, kind: 'comment', quote: 'q', applied: true, detail: '' },
        { index: 1, kind: 'edit', quote: 'q', applied: false, detail: 'free text never sent', reason: 'withheld' },
        { index: 2, kind: 'edit', quote: 'q', applied: false, detail: 'no reason given' },
      ]),
    ).toEqual([
      { index: 0, applied: true, reason: null },
      { index: 1, applied: false, reason: 'withheld' },
      { index: 2, applied: false, reason: 'refused' },
    ]);
  });
});
