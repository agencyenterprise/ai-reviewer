import {
  createThreadChatThreadsPost,
  deleteThreadChatThreadsThreadIdDelete,
  listThreadsChatThreadsGet,
  updateThreadChatThreadsThreadIdPatch,
  type ChatThreadResponse,
} from '@/lib/generated-api';
import { type RemoteThreadListAdapter } from '@assistant-ui/react';
import { createAssistantStream } from 'assistant-stream';

function toMetadata(thread: ChatThreadResponse) {
  return {
    status: thread.is_archived ? ('archived' as const) : ('regular' as const),
    remoteId: thread.id,
    title: thread.title ?? undefined,
  };
}

/**
 * Thread-list metadata backed by our Postgres (via the generated `/chat` SDK).
 * Requests are authenticated by the shared generated client (configured in
 * `ApiConfig`), so no token plumbing is needed here. Per-thread message history
 * is provided separately, inside the runtime hook (see `useChatThreadRuntime`
 * in chat-assistant), because the remote-thread-list runtime calls that hook
 * outside this adapter's `unstable_Provider`.
 */
export const dbThreadListAdapter: RemoteThreadListAdapter = {
  list: async () => {
    const threads = await listThreadsChatThreadsGet();
    return { threads: threads.map(toMetadata) };
  },
  initialize: async () => {
    const thread = await createThreadChatThreadsPost({ body: { title: null } });
    return { remoteId: thread.id, externalId: undefined };
  },
  rename: async (remoteId, newTitle) => {
    await updateThreadChatThreadsThreadIdPatch({ path: { thread_id: remoteId }, body: { title: newTitle } });
  },
  archive: async (remoteId) => {
    await updateThreadChatThreadsThreadIdPatch({ path: { thread_id: remoteId }, body: { is_archived: true } });
  },
  unarchive: async (remoteId) => {
    await updateThreadChatThreadsThreadIdPatch({ path: { thread_id: remoteId }, body: { is_archived: false } });
  },
  delete: async (remoteId) => {
    await deleteThreadChatThreadsThreadIdDelete({ path: { thread_id: remoteId } });
  },
  generateTitle: async (remoteId, messages) => {
    const simpleMessages = messages
      .map((message) => ({
        role: message.role,
        content: message.content.map((part) => (part.type === 'text' ? part.text : '')).join(''),
      }))
      .filter((message) => message.content);

    let title = 'New chat';
    try {
      const response = await fetch('/api/chat/title', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: simpleMessages }),
      });
      if (response.ok) title = (await response.json()).title ?? title;
    } catch {
      // fall back to the default title
    }
    // Persist the generated title so it survives reloads.
    try {
      await updateThreadChatThreadsThreadIdPatch({ path: { thread_id: remoteId }, body: { title } });
    } catch {
      // non-fatal
    }
    return createAssistantStream((controller) => {
      controller.appendText(title);
    });
  },
  fetch: async (remoteId) => {
    const threads = await listThreadsChatThreadsGet();
    const thread = threads.find((row) => row.id === remoteId);
    if (!thread) throw new Error('Thread not found');
    return toMetadata(thread);
  },
};
