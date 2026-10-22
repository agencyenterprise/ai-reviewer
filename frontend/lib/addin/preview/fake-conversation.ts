import type { ChatStreamEvent } from '@/lib/chat/stream';
import type { ChatSuggestion } from '@/lib/generated-api';

/**
 * The pane preview's pretend agent: canned conversations to open on, and replies to
 * what is sent, in the shapes the backend stores (`lib/services/chat/history.py`) and
 * streams (`lib/services/chat/events.py`). Asked for comments or changes, it offers a
 * card and waits on it, as the real agent does (`ask_to_apply`).
 */

export type FakeMessage = Record<string, unknown> & { id: string; type: 'human' | 'ai' | 'tool' };

const human = (id: string, content: string): FakeMessage => ({
  id,
  type: 'human',
  content,
  additional_kwargs: { attachments: [] },
});

const ai = (id: string, text: string, toolCalls: object[] = []): FakeMessage => ({
  id,
  type: 'ai',
  content: text ? [{ type: 'text', text }] : [],
  tool_calls: toolCalls,
});

const ANSWER = `The draft concludes that **air decontamination** is the most cost-effective defence for vital workplaces:

- at 2.5 eACH it removes about 92% of airborne pathogens an hour;
- that is enough to stay ahead of the *silent* scenario, which reaches half of the workforce 35 days sooner than the fast one.

Its weakest link is the cost estimate in Table 2, which rests on a single source.`;

export function cardFor(id: string): ChatSuggestion {
  return {
    id,
    chat_thread_id: 'preview-thread',
    status: 'pending',
    document_name: 'Draft.docx',
    document_url: 'https://contoso.sharepoint.com/sites/Policy/Shared%20Documents/Draft.docx',
    items: {
      comments: [
        {
          quote: 'the scenarios differ in many ways',
          comment: 'Name the differences, or point to where they are set out.',
        },
        { quote: 'at the costs shown in Table 2', comment: 'This rests on one source; say so, or add a second.' },
      ],
      edits: [{ quote: 'It is important to note that the scenarios', replacement: 'The scenarios' }],
    },
    outcome: null,
    created_at: new Date(),
  };
}

/** The messages that offer a card and wait on it, stored as the backend stores them. */
function offering(card: string, intro: string): FakeMessage[] {
  const suggest = { id: `call-suggest-${card}`, name: 'suggest_changes', args: {} };
  const ask = { id: `call-ask-${card}`, name: 'ask_to_apply', args: { suggestion_id: card } };
  return [
    ai(`ai-${card}-1`, intro, [suggest]),
    {
      id: `tool-${card}`,
      type: 'tool',
      tool_call_id: suggest.id,
      name: 'suggest_changes',
      content: JSON.stringify({ saved: true, suggestion_id: card, card: 'new' }),
      status: 'success',
    },
    ai(`ai-${card}-2`, '', [ask]),
  ];
}

export function conversationFor(chat: 'empty' | 'conversation' | 'card'): {
  messages: FakeMessage[];
  pending: string | null;
} {
  if (chat === 'empty') return { messages: [], pending: null };
  const opening = [human('h-1', 'What does this document conclude?'), ai('a-1', ANSWER)];
  if (chat === 'conversation') return { messages: opening, pending: null };
  return {
    messages: [
      ...opening,
      human('h-2', 'Add comments where a claim needs a source.'),
      ...offering('card-1', 'I found two claims that need a source, and one phrase to tighten.'),
    ],
    pending: 'card-1',
  };
}

const ASKS_FOR_CHANGES = /\b(comment|suggest|edit|change|fix|tighten|rewrite)/i;

function textEvents(text: string): ChatStreamEvent[] {
  return (text.match(/.{1,12}(\s|$)|\S+/g) ?? [text]).map((v) => ({ t: 'text', v }));
}

/** The agent's reply to `text`, as the stream sends it and as it is stored afterwards. */
export function previewReply(
  text: string,
  resumed = false,
): { stored: FakeMessage[]; events: ChatStreamEvent[]; card: string | null } {
  if (!resumed && ASKS_FOR_CHANGES.test(text)) {
    const card = `card-${crypto.randomUUID().slice(0, 8)}`;
    const stored = offering(card, 'Here is what I would change.');
    const [first, , second] = stored;
    const suggest = (first.tool_calls as { id: string }[])[0];
    const ask = (second.tool_calls as { id: string; name: string; args: object }[])[0];
    return {
      stored,
      card,
      events: [
        { t: 'message', id: first.id },
        ...textEvents('Here is what I would change.'),
        { t: 'tool', id: suggest.id, name: 'suggest_changes', args: {} },
        { t: 'tool_result', id: suggest.id, name: 'suggest_changes', mid: `tool-${card}`, result: stored[1].content },
        { t: 'message', id: second.id },
        { t: 'tool', id: ask.id, name: ask.name, args: ask.args as Record<string, unknown> },
        { t: 'interrupt', v: [{ suggestion_id: card }] },
      ],
    };
  }
  const id = `ai-${crypto.randomUUID().slice(0, 8)}`;
  const reply = resumed ? text : `${ANSWER}\n\n*(The preview answers every question the same way.)*`;
  return {
    stored: [ai(id, reply)],
    card: null,
    events: [{ t: 'message', id }, ...textEvents(reply), { t: 'message_end', id }],
  };
}
