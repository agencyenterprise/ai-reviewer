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
  /** Every quote in this group, to find the paragraph again at write time. */
  quotes: string[];
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

export function normalize(text: string): string {
  return text.replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/\s+/g, ' ').trim();
}

/** The one paragraph containing `quote`, or why there is not one. */
export function locate(paragraphs: string[], quote: string): number | typeof NOT_FOUND | typeof AMBIGUOUS {
  const wanted = normalize(quote);
  const hits: number[] = [];
  paragraphs.forEach((text, index) => {
    if (wanted && normalize(text).includes(wanted)) hits.push(index);
  });
  if (hits.length === 0) return NOT_FOUND;
  if (hits.length > 1) return AMBIGUOUS;
  return hits[0];
}

function workFor(plan: HandoffPlan, paragraph: number): ParagraphWork {
  let work = plan.paragraphs.get(paragraph);
  if (!work) {
    work = { quotes: [], comments: [], edits: [] };
    plan.paragraphs.set(paragraph, work);
  }
  return work;
}

function unplaced(index: number, kind: AppliedItem['kind'], quote: string, where: string): AppliedItem {
  const reason: FailureReason = where === AMBIGUOUS ? 'ambiguous' : 'not_found';
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
    work.quotes.push(comment.quote);
  });
  edits.forEach((edit, position) => {
    const index = comments.length + position;
    const where = locate(paragraphs, edit.quote);
    if (typeof where !== 'number') {
      plan.unplaced.push(unplaced(index, 'edit', edit.quote, where));
      return;
    }
    const work = workFor(plan, where);
    work.edits.push({ index, edit });
    work.quotes.push(edit.quote);
  });
  return plan;
}

/**
 * The paragraph a group belongs to now. Earlier writes can change a paragraph's text
 * (a tracked deletion still reads as text), so it is found again by any of its quotes
 * rather than trusted to keep its position.
 */
export function relocate(paragraphs: string[], work: ParagraphWork): number | null {
  for (const quote of work.quotes) {
    const where = locate(paragraphs, quote);
    if (typeof where === 'number') return where;
  }
  return null;
}

/** What the server is told: each item's position, whether it landed, and why not. */
export function resultsOf(items: AppliedItem[]): ItemResult[] {
  return items.map(({ index, applied, reason }) => ({
    index,
    applied,
    reason: applied ? null : (reason ?? 'refused'),
  }));
}
