import { describe, expect, it } from 'vitest';
import { lookup, rawSpan, SEARCH_LIMIT } from './quote-search';

describe('rawSpan', () => {
  it('finds a loosely quoted passage in the paragraph’s own characters', () => {
    const text = 'The “best” option — by far,  we think.';
    const span = rawSpan(text, '"best" option - by far, we');
    expect(span && text.slice(span.start, span.end)).toBe('“best” option — by far,  we');
  });

  it('counts an emoji before or inside the quote as one character', () => {
    // Searched in UTF-16 units, sliced in code points: the two must agree.
    const before = '😀 cat dog';
    const span = rawSpan(before, 'cat');
    expect(span && Array.from(before).slice(span.start, span.end).join('')).toBe('cat');

    const inside = 'x a 😀 b y';
    const around = rawSpan(inside, 'a 😀 b');
    expect(around && Array.from(inside).slice(around.start, around.end).join('')).toBe('a 😀 b');
  });

  it('is null when the quote is not there', () => {
    expect(rawSpan('Nothing here.', 'something')).toBeNull();
  });
});

describe('lookup', () => {
  it('searches for a short quote whole, and says which hit it is', () => {
    expect(lookup('a cat and a cat sat', 'a cat sat')).toEqual({ kind: 'whole', search: 'a cat sat', nth: 0, hits: 1 });
    expect(lookup('the cat, the dog, the cat', 'the cat')).toMatchObject({ nth: 0, hits: 2 });
  });

  it('searches for the quote itself after an emoji', () => {
    expect(lookup('😀 cat dog', 'cat')).toEqual({ kind: 'whole', search: 'cat', nth: 0, hits: 1 });
  });

  it('escapes Word’s special character', () => {
    expect(lookup('x ^ y', 'x ^ y')).toMatchObject({ search: 'x ^^ y' });
  });

  it('searches for a long quote by its ends, within Word’s limit', () => {
    const quote = Array.from({ length: 60 }, (_, i) => `word${i}`).join(' ');
    const found = lookup(`Before. ${quote} After.`, quote);
    expect(found).toMatchObject({ kind: 'ends', nth: 0, hits: 1, tailNth: 0 });
    if (found?.kind !== 'ends') throw new Error('expected ends');
    expect(found.head.length).toBeLessThanOrEqual(SEARCH_LIMIT);
    expect(quote.startsWith(found.head)).toBe(true);
    expect(quote.endsWith(found.tail)).toBe(true);
  });

  it('counts a tail that also appears inside a long quote', () => {
    const tail = 'x'.repeat(100);
    const quote = `${tail} ${'y '.repeat(80)}${tail}`;
    expect(lookup(quote, quote)).toMatchObject({ kind: 'ends', tailNth: 1 });
  });
});
