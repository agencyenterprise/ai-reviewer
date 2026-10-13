import { isApiError } from '@/lib/api-error';
import {
  annotateApiMicrosoftWordCommentsAnnotatePost,
  applySuggestionsApiMicrosoftWordSuggestionsApplyPost,
  HandoffView,
} from '@/lib/generated-api';
import {
  AppliedItem,
  CHANGED,
  FailureReason,
  normalize,
  NOT_FOUND,
  ParagraphWork,
  planHandoff,
  relocate,
} from './handoff-plan';
import { paragraphTexts, readParagraphMarkup, scopeText, writeParagraphMarkup } from './word-writes';

/**
 * Write a handoff from Teams into the open document, and say what landed.
 *
 * One read and one write per paragraph however many items it has, because each write
 * is a chance for Word to reject the package. Edits go before comments: a comment whose
 * words an edit removed falls back to the whole paragraph, whereas an edit whose words
 * now carry comment markers is still found.
 *
 * `authorize` is asked before every call, so a long run renews its token as it goes.
 * A 401 stops the run instead of being counted against one paragraph: every later call
 * would be refused too, and the caller has to sign in again.
 */
export async function applyHandoff(handoff: HandoffView, authorize: () => Promise<string>): Promise<AppliedItem[]> {
  const plan = planHandoff(await paragraphTexts(), handoff.items.comments ?? [], handoff.items.edits ?? []);
  const outcomes: AppliedItem[] = [...plan.unplaced];

  for (const work of plan.paragraphs.values()) {
    outcomes.push(...(await applyToParagraph(work, authorize)));
  }
  return outcomes.sort((a, b) => a.index - b.index);
}

function failed(work: ParagraphWork, detail: string, reason: FailureReason): AppliedItem[] {
  return [
    ...work.edits.map(
      ({ index, edit }): AppliedItem => ({ index, kind: 'edit', quote: edit.quote, applied: false, detail, reason }),
    ),
    ...work.comments.map(
      ({ index, comment }): AppliedItem => ({
        index,
        kind: 'comment',
        quote: comment.quote,
        applied: false,
        detail,
        reason,
      }),
    ),
  ];
}

async function unchanged(index: number, before: string | null): Promise<boolean> {
  const now = await scopeText(index);
  return before !== null && now !== null && normalize(now) === normalize(before);
}

async function applyToParagraph(work: ParagraphWork, authorize: () => Promise<string>): Promise<AppliedItem[]> {
  const index = relocate(await paragraphTexts(), work);
  if (index === null) return failed(work, NOT_FOUND, 'not_found');

  try {
    const before = await scopeText(index);
    const read = await readParagraphMarkup(index);
    if (!read) return failed(work, NOT_FOUND, 'not_found');
    let markup: string = read;
    const outcomes: AppliedItem[] = [];

    if (work.edits.length) {
      const applied = await applySuggestionsApiMicrosoftWordSuggestionsApplyPost({
        body: { ooxml: markup, edits: work.edits.map(({ edit }) => edit) },
        headers: { Authorization: await authorize() },
      });
      markup = applied.ooxml ?? markup;
      // No markup back means nothing was written, whatever each edit says.
      const written = !!applied.ooxml;
      const withheld = !written && (applied.warnings ?? []).length > 0;
      work.edits.forEach(({ index: position, edit }, i) => {
        const result = applied.edits?.[i];
        const landed = written && !!result?.applied;
        outcomes.push({
          index: position,
          kind: 'edit',
          quote: edit.quote,
          applied: landed,
          detail: landed ? '' : result?.detail || applied.detail || 'the change was not written',
          reason: landed ? undefined : withheld ? 'withheld' : 'refused',
        });
      });
    }

    for (const { index: position, comment } of work.comments) {
      const anchored = await annotateApiMicrosoftWordCommentsAnnotatePost({
        body: { ooxml: markup, quote: comment.quote, comment: comment.comment },
        headers: { Authorization: await authorize() },
      });
      markup = anchored.ooxml ?? markup;
      outcomes.push({
        index: position,
        kind: 'comment',
        quote: comment.quote,
        applied: anchored.anchored,
        detail: anchored.detail ?? '',
        reason: anchored.anchored ? undefined : 'refused',
      });
    }

    if (outcomes.some((outcome) => outcome.applied)) {
      // The write replaces the whole paragraph, or its whole table, with markup made
      // from the earlier read: anything typed into it meanwhile would be lost.
      if (!(await unchanged(index, before))) return failed(work, CHANGED, 'changed');
      await writeParagraphMarkup(index, markup);
    }
    return outcomes;
  } catch (error) {
    if (isApiError(error, 401)) throw error;
    console.error('Could not apply to paragraph', index, error);
    return failed(work, 'Word or the service refused the change', 'not_written');
  }
}
