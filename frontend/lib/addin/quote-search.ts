/**
 * What to ask Word's search for, to find a quote inside one paragraph.
 *
 * Quotes are matched loosely (`normalize`: curly quotes, dashes, runs of space), but
 * Word's search matches the characters as typed. So the quote is first found in the
 * paragraph's own text, and Word is asked for those exact characters. Word's search
 * also takes at most 255 characters: a longer quote is found by its opening and closing
 * words, and the range between them is checked against the quote.
 *
 * Each lookup says how many hits Word should return and which one is the quote. A count
 * that differs means Word reads the paragraph differently from its text (a field, a
 * footnote mark), and the item is reported as not applied.
 */

import { normalize } from './handoff-plan';

/** Word refuses a longer search string. */
export const SEARCH_LIMIT = 255;
/** How much of a long quote's start and end is searched for. Escaping can double it. */
const END_LENGTH = 100;

export type Lookup =
  | { kind: 'whole'; search: string; nth: number; hits: number }
  | {
      kind: 'ends';
      head: string;
      nth: number;
      hits: number;
      /** Searched for from the head's start to the paragraph's end. */
      tail: string;
      tailNth: number;
    };

/** Where `quote` sits in `text`, matched as `normalize` matches it, in `text`'s own characters. */
export function rawSpan(text: string, quote: string): { start: number; end: number } | null {
  const wanted = normalize(quote);
  if (!wanted) return null;
  let flat = '';
  const origin: number[] = [];
  for (const [i, char] of Array.from(text).entries()) {
    if (/\s/.test(char)) {
      if (flat && !flat.endsWith(' ')) {
        flat += ' ';
        origin.push(i);
      }
      continue;
    }
    flat += normalize(char);
    origin.push(i);
  }
  const at = flat.indexOf(wanted);
  if (at < 0) return null;
  return { start: origin[at], end: origin[at + wanted.length - 1] + 1 };
}

/** Non-overlapping occurrences of `needle` in `text` that start before `before`. */
function occurrences(text: string, needle: string, before = Infinity): number {
  let count = 0;
  for (let at = text.indexOf(needle); at >= 0 && at < before; at = text.indexOf(needle, at + needle.length)) count++;
  return count;
}

/** `^` starts Word's special codes (`^t`, `^p`) even in a plain search. */
function escape(text: string): string {
  return text.replaceAll('^', '^^');
}

export function lookup(paragraph: string, quote: string): Lookup | null {
  // Code points, as `rawSpan` counts them, so a surrogate pair is never cut in two.
  const chars = Array.from(paragraph);
  const span = rawSpan(paragraph, quote);
  if (!span) return null;
  const text = chars.join('');
  const before = chars.slice(0, span.start).join('').length;
  const exact = chars.slice(span.start, span.end).join('');

  if (escape(exact).length <= SEARCH_LIMIT) {
    return {
      kind: 'whole',
      search: escape(exact),
      nth: occurrences(text, exact, before),
      hits: occurrences(text, exact),
    };
  }
  const head = chars.slice(span.start, span.start + END_LENGTH).join('');
  const tail = chars.slice(span.end - END_LENGTH, span.end).join('');
  const fromHead = text.slice(before);
  return {
    kind: 'ends',
    head: escape(head),
    nth: occurrences(text, head, before),
    hits: occurrences(text, head),
    tail: escape(tail),
    tailNth: occurrences(fromHead, tail, exact.length - tail.length),
  };
}
