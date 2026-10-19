import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act } from 'react';
import { ApiError } from '@/lib/api-error';
import {
  dismissApiMicrosoftWordHandoffsHandoffIdDismissedPost,
  getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet,
  reportAppliedApiMicrosoftWordHandoffsHandoffIdAppliedPost,
  startApiMicrosoftWordHandoffsHandoffIdStartedPost,
  type ChatSuggestion,
} from '@/lib/generated-api';
import { applyHandoff } from '@/lib/addin/apply-handoff';
import { flush, renderInto, Rendered, testQueryClient, withQueryClient } from '@/lib/test-render';
import { AddinSessionContext, PausedAnswerContext } from './session-context';
import { cardToShow, SuggestionCard, suggestionResult } from './suggestion-card';

vi.mock('@/lib/generated-api', async (original) => ({
  ...(await original<typeof import('@/lib/generated-api')>()),
  getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet: vi.fn(),
  reportAppliedApiMicrosoftWordHandoffsHandoffIdAppliedPost: vi.fn(),
  dismissApiMicrosoftWordHandoffsHandoffIdDismissedPost: vi.fn(),
  startApiMicrosoftWordHandoffsHandoffIdStartedPost: vi.fn(),
}));
vi.mock('@/lib/addin/apply-handoff', () => ({ applyHandoff: vi.fn() }));

const get = vi.mocked(getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet);
const start = vi.mocked(startApiMicrosoftWordHandoffsHandoffIdStartedPost);
const report = vi.mocked(reportAppliedApiMicrosoftWordHandoffsHandoffIdAppliedPost);
const dismiss = vi.mocked(dismissApiMicrosoftWordHandoffsHandoffIdDismissedPost);
const apply = vi.mocked(applyHandoff);

const ID = 'a7d3c1e0-0000-4000-8000-000000000001';
const expire = vi.fn();
const session = { email: 'ana@contoso.com', authorize: async () => 'Bearer tok', expire };

const suggestion = (overrides: Partial<ChatSuggestion> = {}): ChatSuggestion => ({
  id: ID,
  status: 'pending',
  document_name: 'Draft.docx',
  document_url: 'https://contoso.sharepoint.com/Draft.docx',
  items: {
    comments: [{ quote: 'the only option', comment: 'Overclaims.' }],
    edits: [{ quote: 'recieve', replacement: 'receive' }],
  },
  created_at: new Date('2026-10-15T12:00:00Z'),
  ...overrides,
});

let rendered: Rendered | null = null;

const resume = vi.fn();

let client = testQueryClient();

async function render(waitingOn: string | null = null): Promise<HTMLElement> {
  client = testQueryClient();
  rendered = await renderInto(
    withQueryClient(
      client,
      <AddinSessionContext.Provider value={session}>
        <PausedAnswerContext.Provider
          value={{ pendingSuggestionId: waitingOn, resume, resuming: false, resumedCard: null }}
        >
          <SuggestionCard id={ID} />
        </PausedAnswerContext.Provider>
      </AddinSessionContext.Provider>,
    ),
  );
  await flush();
  return rendered.container;
}

async function click(container: HTMLElement, label: string): Promise<void> {
  const button = [...container.querySelectorAll('button')].find((b) => b.textContent?.includes(label));
  if (!button) throw new Error(`no "${label}" button in: ${container.textContent}`);
  await act(async () => button.click());
  await flush();
}

beforeEach(() => {
  start.mockResolvedValue(undefined as never);
  report.mockResolvedValue(undefined as never);
  dismiss.mockResolvedValue(undefined as never);
});

afterEach(async () => {
  await rendered?.unmount();
  rendered = null;
  vi.resetAllMocks();
});

describe('cardToShow', () => {
  const opened = JSON.stringify({ saved: true, suggestion_id: ID, card: 'new' });
  const added = JSON.stringify({ saved: true, suggestion_id: ID, card: 'added' });

  it('shows the card once, at the call that opened it', () => {
    expect(cardToShow(opened, false)).toBe(ID);
    expect(cardToShow(added, false)).toBeNull();
  });

  it('shows nothing while the answer is still being written', () => {
    expect(cardToShow(opened, true)).toBeNull();
  });

  it('while an answer carries on, shows only the card it waited on, not cards it opens again', () => {
    const retry = JSON.stringify({ saved: true, suggestion_id: 'retry-card', card: 'new' });
    const retryAdded = JSON.stringify({ saved: true, suggestion_id: 'retry-card', card: 'added' });
    expect(cardToShow(opened, true, ID)).toBe(ID);
    expect(cardToShow(retry, true, ID)).toBeNull();
    expect(cardToShow(retryAdded, true, ID)).toBeNull();
    // Once the answer has finished, the new card shows, with every batch on it.
    expect(cardToShow(retry, false, null)).toBe('retry-card');
  });

  it('shows nothing for a call that stored nothing', () => {
    expect(cardToShow(JSON.stringify({ saved: false, message: 'Nothing was saved.' }), false)).toBeNull();
  });

  it('still shows a card stored before cards were per answer', () => {
    expect(cardToShow(JSON.stringify({ saved: true, suggestion_id: ID }), false)).toBe(ID);
  });
});

describe('suggestionResult', () => {
  it('reads the id from the tool result, as a string or already parsed', () => {
    expect(suggestionResult(`{"saved": true, "suggestion_id": "${ID}"}`)?.suggestion_id).toBe(ID);
    expect(suggestionResult({ saved: false, message: 'Nothing was saved' })?.saved).toBe(false);
    expect(suggestionResult('not json')).toBeNull();
  });
});

describe('SuggestionCard', () => {
  it('Apply claims the suggestion, writes it, reports it, and then shows what landed', async () => {
    get.mockResolvedValueOnce(suggestion());
    apply.mockResolvedValue([
      { index: 0, kind: 'comment', quote: 'the only option', applied: true, detail: '' },
      {
        index: 1,
        kind: 'edit',
        quote: 'recieve',
        applied: false,
        detail: 'the words are no longer in the document',
        reason: 'not_found',
      },
    ]);
    get.mockResolvedValueOnce(
      suggestion({
        status: 'applied',
        outcome: {
          items: [
            { kind: 'comment', quote: 'the only option', applied: true, detail: '' },
            {
              kind: 'edit',
              quote: 'recieve',
              applied: false,
              detail: 'the words are no longer in the document',
            },
          ],
        },
      }),
    );
    const container = await render();

    await click(container, 'Apply');

    expect(start).toHaveBeenCalledWith({ path: { handoff_id: ID }, headers: { Authorization: 'Bearer tok' } });
    expect(apply).toHaveBeenCalledWith(expect.objectContaining({ id: ID }));
    expect(report).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { handoff_id: ID },
        body: {
          results: [
            { index: 0, applied: true, reason: null },
            { index: 1, applied: false, reason: 'not_found' },
          ],
        },
      }),
    );
    expect(get).toHaveBeenCalledTimes(2);
    expect(container.textContent).toContain('Applied 1 of 2');
    expect(container.textContent).not.toContain('Dismiss');
  });

  it('Dismiss closes it, and it stays closed when the chat is reloaded', async () => {
    get.mockResolvedValueOnce(suggestion());
    get.mockResolvedValueOnce(suggestion({ status: 'dismissed' }));
    const container = await render();

    await click(container, 'Dismiss');

    expect(dismiss).toHaveBeenCalledWith({ path: { handoff_id: ID }, headers: { Authorization: 'Bearer tok' } });
    expect(apply).not.toHaveBeenCalled();
    expect(container.textContent).toContain('Dismissed: 1 comment and 1 tracked change not added');
  });

  it('an expired suggestion offers nothing to apply', async () => {
    get.mockRejectedValue(new ApiError(404));
    const container = await render();

    expect(container.textContent).toContain('no longer available');
    expect(container.querySelector('button')).toBeNull();
  });

  it('a refused sign-in sends the pane back to sign in', async () => {
    get.mockRejectedValue(new ApiError(401));
    await render();

    expect(expire).toHaveBeenCalled();
  });
});

describe('SuggestionCard on a paused answer', () => {
  it('carries the answer on once the card it waits on is dismissed', async () => {
    get.mockResolvedValueOnce(suggestion());
    get.mockResolvedValueOnce(suggestion({ status: 'dismissed' }));
    const container = await render(ID);

    await click(container, 'Dismiss');

    expect(resume).toHaveBeenCalledTimes(1);
  });

  it('carries the answer on once the card it waits on is applied and reported', async () => {
    get.mockResolvedValueOnce(suggestion());
    apply.mockResolvedValue([{ index: 0, kind: 'comment', quote: 'the only option', applied: true, detail: '' }]);
    get.mockResolvedValueOnce(suggestion({ status: 'applied', outcome: { items: [] } }));
    const container = await render(ID);

    await click(container, 'Apply');

    expect(report).toHaveBeenCalled();
    expect(resume).toHaveBeenCalledTimes(1);
  });

  it('does not touch an answer that waits on another card', async () => {
    get.mockResolvedValueOnce(suggestion());
    get.mockResolvedValueOnce(suggestion({ status: 'dismissed' }));
    const container = await render('another-card');

    await click(container, 'Dismiss');

    expect(resume).not.toHaveBeenCalled();
  });
});

describe('SuggestionCard while its own Apply runs', () => {
  it('does not call its own run interrupted when the server reports it as applying', async () => {
    get.mockResolvedValueOnce(suggestion());
    get.mockResolvedValue(suggestion({ status: 'applying' }));
    apply.mockReturnValue(new Promise(() => {})); // still writing
    const container = await render();

    await click(container, 'Apply');
    // The card is read again mid-Apply (the pane regained focus, say): the server now
    // says `applying`, which is this very run.
    await act(async () => client.refetchQueries());
    await flush();

    expect(container.textContent).toContain('Applying…');
    expect(container.textContent).not.toContain('did not finish');
  });
});
