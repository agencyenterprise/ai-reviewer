import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AssistantRuntimeProvider, useExternalMessageConverter, useExternalStoreRuntime } from '@assistant-ui/react';
import { Thread } from '@/components/assistant-ui/elements/thread.aui';
import { convertChatMessage, type ChatMessage } from '@/lib/chat/turn';
import {
  getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet,
  listChecksApiMicrosoftWordChatChecksGet,
} from '@/lib/generated-api';
import { flush, renderInto, Rendered, testQueryClient, withQueryClient } from '@/lib/test-render';
import { PANE_CONFIG, PANE_THREAD_COMPONENTS } from './pane-thread-config';
import { AddinSessionContext } from './session-context';

vi.mock('@/lib/generated-api', async (original) => ({
  ...(await original<typeof import('@/lib/generated-api')>()),
  getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet: vi.fn(),
  listChecksApiMicrosoftWordChatChecksGet: vi.fn(),
}));

const ID = 'a7d3c1e0-0000-4000-8000-000000000001';
const session = { email: 'ana@contoso.com', authorize: async () => 'Bearer tok', expire: vi.fn() };

// One turn as the backend stores it: reasoning, a file read, then the suggestions.
const HISTORY: ChatMessage[] = [
  { id: 'u1', type: 'human', content: 'Comment on the findings' },
  {
    id: 'a1',
    type: 'ai',
    content: [
      { type: 'reasoning', summary: [{ type: 'summary_text', text: '**Reading**\n\nLooking at the findings.' }] },
    ],
    tool_calls: [
      { id: 'c1', name: 'read_file', args: { file_path: '/documents/document.md' } },
      { id: 'c2', name: 'suggest_changes', args: { comments: [], edits: [] } },
      { id: 'c3', name: 'suggest_changes', args: { comments: [], edits: [] } },
    ],
  },
  { id: 't1', type: 'tool', tool_call_id: 'c1', name: 'read_file', content: '## Findings', status: 'success' },
  {
    id: 't2',
    type: 'tool',
    tool_call_id: 'c2',
    name: 'suggest_changes',
    content: JSON.stringify({ saved: true, suggestion_id: ID, card: 'new' }),
    status: 'success',
  },
  {
    id: 't3',
    type: 'tool',
    tool_call_id: 'c3',
    name: 'suggest_changes',
    // A second batch of the same answer, added to the same card.
    content: JSON.stringify({ saved: true, suggestion_id: ID, card: 'added' }),
    status: 'success',
  },
  { id: 'a2', type: 'ai', content: [{ type: 'text', text: 'I suggested one comment.' }], tool_calls: [] },
];

function Harness({ isRunning = false }: { isRunning?: boolean }) {
  const messages = useExternalMessageConverter({ callback: convertChatMessage, messages: HISTORY, isRunning });
  const runtime = useExternalStoreRuntime({ messages, isRunning, onNew: async () => {} });
  return (
    <AddinSessionContext.Provider value={session}>
      <AssistantRuntimeProvider runtime={runtime} config={PANE_CONFIG}>
        <Thread components={PANE_THREAD_COMPONENTS} />
      </AssistantRuntimeProvider>
    </AddinSessionContext.Provider>
  );
}

let rendered: Rendered | null = null;

beforeEach(async () => {
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
  Element.prototype.scrollIntoView = () => {};
  Element.prototype.scrollTo = () => {};
  vi.mocked(listChecksApiMicrosoftWordChatChecksGet).mockResolvedValue([]);
  vi.mocked(getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet).mockResolvedValue({
    id: ID,
    status: 'pending',
    document_name: 'Draft.docx',
    document_url: 'https://contoso.sharepoint.com/Draft.docx',
    items: { comments: [{ quote: 'the only option', comment: 'Overclaims.' }], edits: [] },
    created_at: new Date('2026-10-15T12:00:00Z'),
  });
  rendered = await renderInto(withQueryClient(testQueryClient(), <Harness />));
  await flush();
  await flush();
});

afterEach(async () => {
  await rendered?.unmount();
  rendered = null;
  vi.unstubAllGlobals();
  vi.resetAllMocks();
});

describe('the pane thread', () => {
  it("shows the answer's one card, once, in the answer rather than in the chain of thought", () => {
    const applies = [...document.querySelectorAll('button')].filter((button) => button.textContent === 'Apply');
    const apply = applies[0];

    expect(applies).toHaveLength(1);
    expect(apply?.closest('[data-slot="aui_chain-of-thought"]')).toBeNull();
    expect(document.querySelector('[data-slot="aui_chain-of-thought"]')).not.toBeNull();
  });

  it('shows no card while the answer is still being written', async () => {
    await rendered?.unmount();
    vi.mocked(getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet).mockClear();
    rendered = await renderInto(withQueryClient(testQueryClient(), <Harness isRunning />));
    await flush();

    const applies = [...document.querySelectorAll('button')].filter((button) => button.textContent === 'Apply');
    expect(applies).toHaveLength(0);
    expect(getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet).not.toHaveBeenCalled();
  });
});
