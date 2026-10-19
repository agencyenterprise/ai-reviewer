import { describe, expect, it } from 'vitest';
import { AMBIGUOUS, NOT_FOUND, locate, planHandoff } from './handoff-plan';

const paragraphs = [
  'Introduction',
  'The  results show that   this is the only option.',
  'We recieve funding from two sources.',
  'Funding is discussed below.',
];

describe('locate', () => {
  it('finds a quote whatever its whitespace', () => {
    expect(locate(paragraphs, 'results show that this is')).toBe(1);
  });

  it('treats curly and straight quotes alike', () => {
    expect(locate(["the author's view"], 'the author’s view')).toBe(0);
  });

  it('treats hyphens and en or em dashes alike', () => {
    expect(locate(['Site specific - BTM'], 'Site specific – BTM')).toBe(0);
    expect(locate(['a long—winded clause'], 'long-winded')).toBe(0);
  });

  it('reports a quote that is gone', () => {
    expect(locate(paragraphs, 'no such words')).toBe(NOT_FOUND);
  });

  it('refuses to choose between two paragraphs', () => {
    expect(locate(paragraphs, 'unding')).toBe(AMBIGUOUS);
  });

  it('refuses to choose between two places in one paragraph', () => {
    expect(locate(['Then the rate rose, and the rate fell.'], 'the rate')).toBe(AMBIGUOUS);
  });
});

describe('planHandoff', () => {
  it('groups by paragraph and reports what cannot be placed', () => {
    const plan = planHandoff(
      paragraphs,
      [
        { quote: 'the only option', comment: 'Overclaims.' },
        { quote: 'vanished text', comment: 'x' },
      ],
      [{ quote: 'recieve', replacement: 'receive' }],
    );

    expect([...plan.paragraphs.keys()].sort()).toEqual([1, 2]);
    // Each item keeps its position in the handoff: comments first, then edits.
    expect(plan.paragraphs.get(1)?.comments.map(({ index }) => index)).toEqual([0]);
    expect(plan.paragraphs.get(2)?.edits.map(({ index }) => index)).toEqual([2]);
    expect(plan.unplaced).toEqual([
      { index: 1, kind: 'comment', quote: 'vanished text', applied: false, detail: NOT_FOUND, reason: 'not_found' },
    ]);
  });
});
