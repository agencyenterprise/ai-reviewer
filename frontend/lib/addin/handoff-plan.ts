import { HandoffComment, HandoffEdit, ItemResult } from '@/lib/generated-api';

/**
 * Where each of a handoff's comments and edits goes, worked out from the paragraphs'
 * text before anything is written.
 *
 * Items are placed by quote because the review was done on an earlier copy of the
 * document: a quote is either still there or it is not, where a paragraph number would
 * silently point somewhere else. A quote found in more than one paragraph is not
 * guessed at either.
 *
 * Every item keeps its position in the handoff (comments first, then edits): that is
 * how its result is reported, so the server can word the report from what it stored.
 */

export type FailureReason = NonNullable<ItemResult['reason']>;

/** What happened to one item: `detail` is shown in the pane, `reason` is reported. */
export type AppliedItem = {
  index: number;
  kind: 'comment' | 'edit';
  quote: string;
  applied: boolean;
  detail: string;
  reason?: FailureReason;
};

export type ParagraphWork = {
  comments: { index: number; comment: HandoffComment }[];
  edits: { index: number; edit: HandoffEdit }[];
};

export type HandoffPlan = {
  paragraphs: Map<number, ParagraphWork>;
  /** Items that cannot be placed, already reported as not applied. */
  unplaced: AppliedItem[];
};

export const NOT_FOUND = 'the words are no longer in the document';
export const AMBIGUOUS = 'the words appear in more than one paragraph';
export const OVERLAPS = 'it overlaps another edit, which would change its words first';

/**
 * Text as quotes are compared: curly quotes, dashes and runs of space evened out. Kept
 * the same as `normalize` in `lib/services/microsoft/word/quote_check.py`, which checks
 * the chat agent's quotes before they are offered.
 */
export function normalize(text: string): string {
  return text
    .replace(/[‘’]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[‐‑‒–—―−]/g, '-')
    .replace(/\s+/g, ' ')
    .trim();
}

/** The one paragraph containing `quote`, once, or why there is not one. */
export function locate(paragraphs: string[], quote: string): number | typeof NOT_FOUND | typeof AMBIGUOUS {
  const wanted = normalize(quote);
  // Each occurrence, not each paragraph: twice in one paragraph is as ambiguous as
  // once in each of two, since a write would land on the first.
  const hits: number[] = [];
  paragraphs.forEach((text, index) => {
    if (!wanted) return;
    const found = occurrences(normalize(text), wanted);
    for (let i = 0; i < found; i++) hits.push(index);
  });
  if (hits.length === 0) return NOT_FOUND;
  if (hits.length > 1) return AMBIGUOUS;
  return hits[0];
}

function workFor(plan: HandoffPlan, paragraph: number): ParagraphWork {
  let work = plan.paragraphs.get(paragraph);
  if (!work) {
    work = { comments: [], edits: [] };
    plan.paragraphs.set(paragraph, work);
  }
  return work;
}

function unplaced(index: number, kind: AppliedItem['kind'], quote: string, where: string): AppliedItem {
  const reason: FailureReason = where === AMBIGUOUS ? 'ambiguous' : where === OVERLAPS ? 'withheld' : 'not_found';
  return { index, kind, quote, applied: false, detail: where, reason };
}

export function planHandoff(paragraphs: string[], comments: HandoffComment[], edits: HandoffEdit[]): HandoffPlan {
  const plan: HandoffPlan = { paragraphs: new Map(), unplaced: [] };
  comments.forEach((comment, position) => {
    const where = locate(paragraphs, comment.quote);
    if (typeof where !== 'number') {
      plan.unplaced.push(unplaced(position, 'comment', comment.quote, where));
      return;
    }
    const work = workFor(plan, where);
    work.comments.push({ index: position, comment });
  });
  edits.forEach((edit, position) => {
    const index = comments.length + position;
    const where = locate(paragraphs, edit.quote);
    if (typeof where !== 'number') {
      plan.unplaced.push(unplaced(index, 'edit', edit.quote, where));
      return;
    }
    const work = workFor(plan, where);
    // Every range is found before anything is written, so an edit whose words another
    // edit replaces first would land on that edit's text.
    if (work.edits.some((other) => overlap(paragraphs[where], other.edit.quote, edit.quote))) {
      plan.unplaced.push(unplaced(index, 'edit', edit.quote, OVERLAPS));
      return;
    }
    work.edits.push({ index, edit });
  });
  return plan;
}

/** Whether two quotes, each once in `paragraph`, share any of its words. */
function overlap(paragraph: string, first: string, second: string): boolean {
  const text = normalize(paragraph);
  const [a, b] = [normalize(first), normalize(second)];
  const [startA, startB] = [text.indexOf(a), text.indexOf(b)];
  return startA < startB + b.length && startB < startA + a.length;
}

/** How many times `wanted` starts in `text`, overlapping ones included: `ana` is twice in `banana`. */
export function occurrences(text: string, wanted: string): number {
  let count = 0;
  for (let at = text.indexOf(wanted); at !== -1; at = text.indexOf(wanted, at + 1)) count++;
  return count;
}

/** What the server is told: each item's position, whether it landed, and why not. */
export function resultsOf(items: AppliedItem[]): ItemResult[] {
  return items.map(({ index, applied, reason }) => ({
    index,
    applied,
    reason: applied ? null : (reason ?? 'refused'),
  }));
}
