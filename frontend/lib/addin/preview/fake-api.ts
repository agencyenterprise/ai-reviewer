import type { ChatSuggestion, HandoffView, PaneCheck } from '@/lib/generated-api';
import { conversationFor, cardFor, previewReply, type FakeMessage } from './fake-conversation';
import type { PreviewScenario } from './scenario';

/**
 * The add-in's API as the pane preview answers it, in the browser: every request under
 * `/api/microsoft/word/` is answered from memory, in the shapes the real routes return
 * (`lib/api/routers/microsoft/word.py`, `word_chat.py`). Anything else goes out as usual.
 *
 * Stateful, as the backend is: a message sent is stored and answered, a card dismissed
 * stays dismissed, and New chat starts over. A reload starts the scenario again.
 */

export const PREVIEW_DOCUMENT_URL = 'https://contoso.sharepoint.com/sites/Policy/Shared%20Documents/Draft.docx';
const WORD = '/api/microsoft/word';

const CHECKS: PaneCheck[] = [
  {
    skill: 'abbreviation-scan',
    name: 'Abbreviations',
    description: 'Defined at first use, listed, used consistently.',
  },
  {
    skill: 'figures-tables-check',
    name: 'Figures & Tables',
    description: 'Titled, numbered and referenced in the text.',
  },
  { skill: 'advocacy-tone', name: 'Advocacy Tone', description: 'Neutral, objective language throughout.' },
];

function handoff(id: string, url: string, name: string, comments: number, edits: number): HandoffView {
  return {
    id,
    status: 'pending',
    document_name: name,
    document_url: url,
    items: {
      comments: Array.from({ length: comments }, (_, i) => ({
        quote: `the scenarios differ in many ways${i ? ` (${i + 1})` : ''}`,
        comment: 'Say how they differ, or cite where the reader can find out.',
      })),
      edits: Array.from({ length: edits }, () => ({
        quote: 'It is important to note that the scenarios',
        replacement: 'The scenarios',
      })),
    },
    created_at: new Date('2026-10-22T14:14:00Z'),
  };
}

function teamsHandoffs(scenario: PreviewScenario): { here: HandoffView[]; elsewhere: HandoffView[] } {
  const here = ['here', 'both'].includes(scenario.waiting)
    ? [
        handoff('teams-1', PREVIEW_DOCUMENT_URL, 'Draft.docx', 2, 1),
        handoff('teams-2', PREVIEW_DOCUMENT_URL, 'Draft.docx', 1, 0),
      ]
    : [];
  const other = 'https://contoso.sharepoint.com/sites/Policy/Shared%20Documents/v3-cern-for-ai.docx';
  const elsewhere = ['elsewhere', 'both'].includes(scenario.waiting)
    ? [handoff('teams-3', other, 'v3-cern-for-ai.docx', 3, 0)]
    : [];
  return { here, elsewhere };
}

type State = {
  messages: FakeMessage[];
  pending: string | null;
  cards: Map<string, ChatSuggestion>;
  handoffs: { here: HandoffView[]; elsewhere: HandoffView[] };
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

const NO_CONTENT = () => new Response(null, { status: 204 });

/** A server-sent event stream of `events`, paced like a model typing. */
function eventStream(events: object[]): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    async start(controller) {
      for (const event of events) {
        await new Promise((resolve) => setTimeout(resolve, 'v' in event ? 25 : 120));
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
      }
      controller.close();
    },
  });
  return new Response(body, { status: 200, headers: { 'Content-Type': 'text/event-stream' } });
}

/** Answer the add-in's API from memory for this page. Returns a function that stops it. */
export function installFakeApi(scenario: PreviewScenario): () => void {
  const conversation = conversationFor(scenario.chat);
  const state: State = {
    messages: conversation.messages,
    pending: conversation.pending,
    cards: new Map(conversation.pending ? [[conversation.pending, cardFor(conversation.pending)]] : []),
    handoffs: teamsHandoffs(scenario),
  };
  const real = window.fetch.bind(window);

  async function answer(path: string, method: string, body: BodyInit | null | undefined): Promise<Response> {
    if (path === `${WORD}/features`) return json({ teams: scenario.teams });
    if (path === `${WORD}/handoffs`) return json(state.handoffs);
    const handoffAction = path.match(new RegExp(`^${WORD}/handoffs/([^/]+)/(started|applied|dismissed)$`));
    if (handoffAction) return settle(handoffAction[1], handoffAction[2]);
    if (path === `${WORD}/chat/checks`) return json(CHECKS);
    if (path === `${WORD}/chat/thread`) {
      return json({
        thread_id: state.messages.length ? 'preview-thread' : null,
        messages: state.messages,
        pending_suggestion_id: state.pending,
      });
    }
    const suggestion = path.match(new RegExp(`^${WORD}/chat/suggestions/([^/]+)$`));
    if (suggestion) {
      const card = state.cards.get(suggestion[1]);
      return card ? json(card) : json({ detail: 'No suggestions with that id' }, 404);
    }
    if (path === `${WORD}/chat/thread/clear` && method === 'POST') {
      state.messages = [];
      state.pending = null;
      return NO_CONTENT();
    }
    if (path === `${WORD}/chat/thread/stream` && method === 'POST') return stream(body);
    if (path === `${WORD}/chat/thread/resume` && method === 'POST') return resume();
    return json({ detail: `The preview does not answer ${method} ${path}` }, 404);
  }

  function settle(id: string, action: string): Response {
    const card = state.cards.get(id);
    if (card && action === 'started') card.status = 'applying';
    if (card && action === 'dismissed') card.status = 'dismissed';
    if (action === 'dismissed' || action === 'applied') {
      state.handoffs = {
        here: state.handoffs.here.filter((h) => h.id !== id),
        elsewhere: state.handoffs.elsewhere.filter((h) => h.id !== id),
      };
    }
    return NO_CONTENT();
  }

  async function stream(body: BodyInit | null | undefined): Promise<Response> {
    if (!scenario.key) {
      return json(
        {
          detail:
            'Draft Detective needs your OpenAI API key to answer. Sign in to https://draftdetective.example.com/account ' +
            "with this Microsoft account's email address and add it there, then ask again.",
        },
        403,
      );
    }
    const form = body instanceof FormData ? body : null;
    const text = String(form?.get('message') ?? '');
    const id = String(form?.get('message_id') ?? crypto.randomUUID());
    state.messages = [...state.messages, { id, type: 'human', content: text, additional_kwargs: { attachments: [] } }];
    const reply = previewReply(text);
    state.messages = [...state.messages, ...reply.stored];
    if (reply.card) {
      state.pending = reply.card;
      state.cards.set(reply.card, cardFor(reply.card));
    }
    return eventStream(reply.events);
  }

  function resume(): Response {
    const card = state.pending ? state.cards.get(state.pending) : undefined;
    state.pending = null;
    const said = card?.status === 'dismissed' ? 'Understood: I left those out.' : 'Those are in the document now.';
    const reply = previewReply(said, true);
    state.messages = [...state.messages, ...reply.stored];
    return eventStream(reply.events);
  }

  window.fetch = async (input, init) => {
    const request = input instanceof Request ? input : null;
    const url = new URL(request?.url ?? (input instanceof URL ? input.href : String(input)), window.location.href);
    if (!url.pathname.startsWith(WORD)) return real(input, init);
    const method = (init?.method ?? request?.method ?? 'GET').toUpperCase();
    return answer(
      url.pathname,
      method,
      init?.body ?? (request?.body ? await request.formData().catch(() => null) : null),
    );
  };
  return () => {
    window.fetch = real;
  };
}
