import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/lib/api-error';
import type { HandoffView } from '@/lib/generated-api';

const word = vi.hoisted(() => ({
  paragraphTexts: vi.fn(),
  readParagraphMarkup: vi.fn(),
  writeParagraphMarkup: vi.fn(),
  scopeText: vi.fn(),
}));
const api = vi.hoisted(() => ({
  annotateApiMicrosoftWordCommentsAnnotatePost: vi.fn(),
  applySuggestionsApiMicrosoftWordSuggestionsApplyPost: vi.fn(),
}));

vi.mock('./word-writes', () => word);
vi.mock('@/lib/generated-api', () => api);

import { applyHandoff } from './apply-handoff';
import { AMBIGUOUS, CHANGED, NOT_FOUND, resultsOf } from './handoff-plan';

const PARAGRAPHS = ['Introduction', 'We recieve funding and this is the only option.', 'Funding is discussed below.'];
const authorize = vi.fn();

function handoff(items: HandoffView['items']): HandoffView {
  return {
    id: 'h1',
    status: 'pending',
    document_name: 'Draft.docx',
    document_url: 'https://x',
    items,
    created_at: new Date('2026-10-09T00:00:00Z'),
  };
}

beforeEach(() => {
  vi.resetAllMocks();
  authorize.mockResolvedValue('Bearer t');
  word.paragraphTexts.mockResolvedValue(PARAGRAPHS);
  word.readParagraphMarkup.mockResolvedValue('<in/>');
  word.scopeText.mockResolvedValue('the paragraph as read');
  api.applySuggestionsApiMicrosoftWordSuggestionsApplyPost.mockResolvedValue({
    applied: 1,
    ooxml: '<edited/>',
    edits: [{ quote: 'recieve', applied: true, detail: '' }],
  });
  api.annotateApiMicrosoftWordCommentsAnnotatePost.mockResolvedValue({
    anchored: true,
    ooxml: '<edited-and-commented/>',
    detail: '',
  });
});

describe('applyHandoff', () => {
  it('writes edits then comments into one paragraph, with one read and one write', async () => {
    const items = await applyHandoff(
      handoff({
        comments: [{ quote: 'the only option', comment: 'Overclaims.' }],
        edits: [{ quote: 'recieve', replacement: 'receive' }],
      }),
      authorize,
    );

    expect(word.readParagraphMarkup).toHaveBeenCalledTimes(1);
    expect(word.readParagraphMarkup).toHaveBeenCalledWith(1);
    // The comment is written into the markup the edits produced, not the original.
    expect(api.annotateApiMicrosoftWordCommentsAnnotatePost.mock.calls[0][0].body.ooxml).toBe('<edited/>');
    expect(word.writeParagraphMarkup).toHaveBeenCalledTimes(1);
    expect(word.writeParagraphMarkup).toHaveBeenCalledWith(1, '<edited-and-commented/>');
    // By position in the handoff: comments first, then edits.
    expect(items.map((item) => [item.index, item.kind, item.applied])).toEqual([
      [0, 'comment', true],
      [1, 'edit', true],
    ]);
  });

  it('asks for a token before every call, so a long run renews it', async () => {
    authorize.mockResolvedValueOnce('Bearer first').mockResolvedValue('Bearer renewed');
    await applyHandoff(
      handoff({
        comments: [{ quote: 'the only option', comment: 'x' }],
        edits: [{ quote: 'recieve', replacement: 'receive' }],
      }),
      authorize,
    );

    expect(api.applySuggestionsApiMicrosoftWordSuggestionsApplyPost.mock.calls[0][0].headers).toEqual({
      Authorization: 'Bearer first',
    });
    expect(api.annotateApiMicrosoftWordCommentsAnnotatePost.mock.calls[0][0].headers).toEqual({
      Authorization: 'Bearer renewed',
    });
  });

  it('reports words that are gone or ambiguous without calling the service', async () => {
    const items = await applyHandoff(
      handoff({ comments: [{ quote: 'unding', comment: 'x' }], edits: [{ quote: 'vanished', replacement: 'y' }] }),
      authorize,
    );

    expect(api.applySuggestionsApiMicrosoftWordSuggestionsApplyPost).not.toHaveBeenCalled();
    expect(word.writeParagraphMarkup).not.toHaveBeenCalled();
    expect(items.map((item) => [item.detail, item.reason])).toEqual([
      [AMBIGUOUS, 'ambiguous'],
      [NOT_FOUND, 'not_found'],
    ]);
  });

  it('writes nothing when nothing landed', async () => {
    api.annotateApiMicrosoftWordCommentsAnnotatePost.mockResolvedValue({ anchored: false, detail: 'no text' });

    const items = await applyHandoff(handoff({ comments: [{ quote: 'the only option', comment: 'x' }] }), authorize);

    expect(word.writeParagraphMarkup).not.toHaveBeenCalled();
    expect(items[0]).toMatchObject({ applied: false, detail: 'no text', reason: 'refused' });
  });

  it('an edit the service withheld is reported as withheld, and nothing is written', async () => {
    api.applySuggestionsApiMicrosoftWordSuggestionsApplyPost.mockResolvedValue({
      applied: 0,
      ooxml: null,
      edits: [{ quote: 'recieve', applied: true, detail: '' }],
      detail: 'The change would have altered text it should not have',
      warnings: ['rejecting the changes would not restore the original'],
    });

    const items = await applyHandoff(handoff({ edits: [{ quote: 'recieve', replacement: 'receive' }] }), authorize);

    expect(items[0]).toMatchObject({ applied: false, reason: 'withheld' });
    expect(word.writeParagraphMarkup).not.toHaveBeenCalled();
  });

  it('reports every item in a paragraph Word refused', async () => {
    word.writeParagraphMarkup.mockRejectedValue(new Error('GeneralException'));
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    const items = await applyHandoff(
      handoff({
        comments: [{ quote: 'the only option', comment: 'x' }],
        edits: [{ quote: 'recieve', replacement: 'receive' }],
      }),
      authorize,
    );

    expect(items).toHaveLength(2);
    expect(items.every((item) => !item.applied && item.reason === 'not_written')).toBe(true);
  });

  it('a refused token stops the run rather than counting against a paragraph', async () => {
    api.applySuggestionsApiMicrosoftWordSuggestionsApplyPost.mockRejectedValue(new ApiError(401));

    await expect(
      applyHandoff(handoff({ edits: [{ quote: 'recieve', replacement: 'receive' }] }), authorize),
    ).rejects.toMatchObject({ status: 401 });
    expect(word.writeParagraphMarkup).not.toHaveBeenCalled();
  });

  it('writes nothing over a paragraph, or table, someone edited while the service worked', async () => {
    word.scopeText.mockResolvedValueOnce('the paragraph as read').mockResolvedValueOnce('a coauthor typed here');

    const items = await applyHandoff(handoff({ edits: [{ quote: 'recieve', replacement: 'receive' }] }), authorize);

    expect(word.writeParagraphMarkup).not.toHaveBeenCalled();
    expect(items[0]).toMatchObject({ applied: false, detail: CHANGED, reason: 'changed' });
  });

  it('reports a paragraph that moved away before it could be written', async () => {
    word.paragraphTexts.mockResolvedValueOnce(PARAGRAPHS).mockResolvedValueOnce(['Introduction', 'Rewritten.']);

    const items = await applyHandoff(handoff({ edits: [{ quote: 'recieve', replacement: 'receive' }] }), authorize);

    expect(word.readParagraphMarkup).not.toHaveBeenCalled();
    expect(items[0]).toMatchObject({ applied: false, detail: NOT_FOUND, reason: 'not_found' });
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
