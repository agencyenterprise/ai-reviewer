import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, useLayoutEffect } from 'react';
import { ApiError } from '@/lib/api-error';
import { documentFile, selectedText } from '@/lib/addin/pane-document';
import { streamWordChatResume, streamWordChatTurn } from '@/lib/addin/word-chat-stream';
import type { ChatStreamEvent } from '@/lib/chat/stream';
import {
  clearThreadApiMicrosoftWordChatThreadClearPost,
  getThreadApiMicrosoftWordChatThreadGet,
} from '@/lib/generated-api';
import { flush, renderInto, Rendered, testQueryClient, withQueryClient } from '@/lib/test-render';
import { useWordChatRuntime } from './use-word-chat-runtime';

vi.mock('@/lib/generated-api', async (original) => ({
  ...(await original<typeof import('@/lib/generated-api')>()),
  getThreadApiMicrosoftWordChatThreadGet: vi.fn(),
  clearThreadApiMicrosoftWordChatThreadClearPost: vi.fn(),
}));
// Two versions of the document, told apart by identity.
const V1 = new Blob(['v1']);
const V2 = new Blob(['v2']);
const VERSIONS = new Map([
  [V1, 'v1'],
  [V2, 'v2'],
]);

vi.mock('@/lib/addin/pane-document', () => ({
  documentFile: vi.fn(),
  selectedText: vi.fn(),
  fingerprint: async (file: Blob) => `fp:${VERSIONS.get(file)}`,
}));
vi.mock('@/lib/addin/word-chat-stream', async (original) => ({
  ...(await original<typeof import('@/lib/addin/word-chat-stream')>()),
  streamWordChatTurn: vi.fn(),
  streamWordChatResume: vi.fn(),
}));

const history = vi.mocked(getThreadApiMicrosoftWordChatThreadGet);
const clearThread = vi.mocked(clearThreadApiMicrosoftWordChatThreadClearPost);
const file = vi.mocked(documentFile);
const selection = vi.mocked(selectedText);
const stream = vi.mocked(streamWordChatTurn);
const resumeStream = vi.mocked(streamWordChatResume);

const URL = 'https://contoso.sharepoint.com/Draft.docx';
const expire = vi.fn();
const session = { email: 'ana@contoso.com', authorize: async () => 'Bearer tok', expire };

type Harness = ReturnType<typeof useWordChatRuntime>;
const seen: { current?: Harness } = {};
let rendered: Rendered | null = null;

// What the pane reads as the document's key when a message is sent.
let keyNow = URL;

function Probe({ seenRef }: { seenRef: { current?: Harness } }) {
  const runtime = useWordChatRuntime(session, URL, () => keyNow);
  useLayoutEffect(() => {
    seenRef.current = runtime;
  });
  return null;
}

async function* answer(): AsyncGenerator<ChatStreamEvent> {
  yield { t: 'message', id: 'ai-1' };
  yield { t: 'text', v: 'Done.' };
  yield { t: 'message_end', id: 'ai-1' };
}

async function send(text: string): Promise<void> {
  await act(async () => {
    seen.current!.runtime.thread.append({ role: 'user', content: [{ type: 'text', text }] });
  });
  await flush();
  await flush();
}

/** What was sent as the document with each message: its version, or undefined. */
const sentDocuments = () =>
  stream.mock.calls.map(([options]) => (options.document ? VERSIONS.get(options.document) : undefined));

beforeEach(async () => {
  history.mockResolvedValue({ thread_id: null, messages: [] });
  clearThread.mockResolvedValue(undefined as never);
  file.mockResolvedValue(V1);
  selection.mockResolvedValue('');
  stream.mockImplementation(() => answer());
  rendered = await renderInto(withQueryClient(testQueryClient(), <Probe seenRef={seen} />));
  await flush();
});

afterEach(async () => {
  await rendered?.unmount();
  rendered = null;
  seen.current = undefined;
  vi.resetAllMocks();
});

describe('useWordChatRuntime', () => {
  it('sends the document with the first message, and again only once it changed', async () => {
    await send('first');
    await send('second');
    file.mockResolvedValue(V2);
    await send('third');

    expect(sentDocuments()).toEqual(['v1', undefined, 'v2']);
    expect(stream.mock.calls[0][0]).toMatchObject({ url: URL, message: 'first', authorization: 'Bearer tok' });
  });

  it('sends the selection along with the message', async () => {
    selection.mockResolvedValue('the only option');
    await send('Is this right?');

    expect(stream.mock.calls[0][0].selection).toBe('the only option');
  });

  it('after clearing, the new conversation gets the document again', async () => {
    await send('first');
    await act(async () => seen.current!.clear.mutate());
    await flush();
    await send('again');

    expect(clearThread).toHaveBeenCalledWith({ body: { url: URL }, headers: { Authorization: 'Bearer tok' } });
    expect(sentDocuments()).toEqual(['v1', 'v1']);
  });

  it('a turn that never started does not count the document as sent', async () => {
    stream.mockImplementationOnce(() => {
      throw new ApiError(500, 'down');
    });
    await send('first');
    await send('again');

    expect(sentDocuments()).toEqual(['v1', 'v1']);
  });

  it('sends the document again when the conversation turns out not to have it', async () => {
    // Sent once; then the server's conversation changed (saved, cleared elsewhere).
    await send('first');
    stream.mockImplementationOnce(() => {
      throw new ApiError(409, 'send the document');
    });
    await send('second');

    expect(sentDocuments()).toEqual(['v1', undefined, 'v1']);
    expect(stream.mock.calls[2][0].message).toBe('second');
  });

  it('a refused sign-in sends the pane back to sign in', async () => {
    stream.mockImplementationOnce(() => {
      throw new ApiError(401);
    });
    await send('first');

    expect(expire).toHaveBeenCalled();
  });

  it('outside Word it still sends the message, without a document', async () => {
    file.mockRejectedValue(new Error('Word is not defined'));
    await send('hello');

    expect(sentDocuments()).toEqual([undefined]);
  });

  it('inside Word a failed read stops the message rather than send it without the document', async () => {
    vi.stubGlobal('Office', { context: { document: {} } });
    try {
      file.mockRejectedValue(new Error('the file is busy'));
      await send('hello');

      // Sent without it, the agent would answer from an older copy.
      expect(stream).not.toHaveBeenCalled();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it('sends to the document as it is now named, with the document again', async () => {
    await send('first');
    keyNow = 'https://contoso.sharepoint.com/Saved as.docx';
    try {
      await send('after Save As');
    } finally {
      keyNow = URL;
    }

    expect(stream.mock.calls.map(([options]) => options.url)).toEqual([
      URL,
      'https://contoso.sharepoint.com/Saved as.docx',
    ]);
    // Another key is another conversation: it has not been sent this document.
    expect(sentDocuments()).toEqual(['v1', 'v1']);
  });

  it('names the card a paused answer waits on, and carries the answer on through resume', async () => {
    history.mockResolvedValue({ thread_id: 't', messages: [], pending_suggestion_id: 'card-1' });
    await rendered?.unmount();
    rendered = await renderInto(withQueryClient(testQueryClient(), <Probe seenRef={seen} />));
    await flush();

    expect(seen.current!.pendingSuggestionId).toBe('card-1');

    history.mockResolvedValue({ thread_id: 't', messages: [], pending_suggestion_id: null });
    resumeStream.mockImplementation(() => answer());
    await act(async () => seen.current!.resume());
    await flush();

    expect(resumeStream).toHaveBeenCalledWith(expect.objectContaining({ url: URL, authorization: 'Bearer tok' }));
    expect(stream).not.toHaveBeenCalled();
    expect(seen.current!.pendingSuggestionId).toBeNull();
  });
});
