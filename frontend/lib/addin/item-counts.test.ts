import { describe, expect, it } from 'vitest';
import { describeItems } from './item-counts';

describe('describeItems', () => {
  it('leaves out a kind there are none of', () => {
    expect(describeItems(0, 2)).toBe('2 tracked changes');
    expect(describeItems(3, 0)).toBe('3 comments');
  });

  it('names both when there are both, singular where it is one', () => {
    expect(describeItems(1, 1)).toBe('1 comment and 1 tracked change');
  });
});
