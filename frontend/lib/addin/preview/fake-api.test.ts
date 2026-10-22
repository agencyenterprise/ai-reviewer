import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_SCENARIO, type PreviewScenario } from './scenario';
import { textEvents } from './fake-conversation';

const WORD = 'http://api.test/api/microsoft/word';
const realFetch = window.fetch;

/** A fresh stand-in: it installs once per page load, so each test loads its own module. */
async function install(scenario: Partial<PreviewScenario> = {}) {
  vi.resetModules();
  const { installFakeApi } = await import('./fake-api');
  installFakeApi({ ...DEFAULT_SCENARIO, ...scenario });
}

function send(message: string, signal?: AbortSignal) {
  const form = new FormData();
  form.append('url', '');
  form.append('message', message);
  return fetch(`${WORD}/chat/thread/stream`, { method: 'POST', body: form, signal });
}

const history = async () => (await (await fetch(`${WORD}/chat/thread`)).json()) as { messages: { type: string }[] };

beforeEach(() => vi.useRealTimers());
afterEach(() => {
  window.fetch = realFetch;
});

describe('the preview stand-in API', () => {
  it('stores an answer only once all of it was sent', async () => {
    await install();
    await (await send('What does this conclude?')).text();

    expect((await history()).messages.map((m) => m.type)).toEqual(['human', 'ai']);
  });

  it('stops an answer when the pane stops it, and keeps only the question', async () => {
    await install();
    const stop = new AbortController();
    const response = await send('What does this conclude?', stop.signal);
    stop.abort();

    await expect(response.text()).rejects.toThrow();
    expect((await history()).messages.map((m) => m.type)).toEqual(['human']);
  });

  it('refuses to carry an answer on without a key, and the card still waits', async () => {
    await install({ chat: 'card', key: false });
    const resumed = await fetch(`${WORD}/chat/thread/resume`, { method: 'POST' });

    expect(resumed.status).toBe(403);
    const after = (await (await fetch(`${WORD}/chat/thread`)).json()) as { pending_suggestion_id: string | null };
    expect(after.pending_suggestion_id).toBe('card-1');
  });
});

describe('textEvents', () => {
  it('streams the text so it joins back exactly, blank lines and all', () => {
    const text = 'A heading\n\n- one;\n- two.\n\n  Indented *and* done.';
    expect(
      textEvents(text)
        .map((event) => ('v' in event ? event.v : ''))
        .join(''),
    ).toBe(text);
  });
});
