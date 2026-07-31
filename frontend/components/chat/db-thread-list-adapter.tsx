'use client';

import { chatThreadsApi, type DbThread } from '@/lib/chat-threads-api';
import { type RemoteThreadListAdapter } from '@assistant-ui/react';
import { createAssistantStream } from 'assistant-stream';
import { useSession } from 'next-auth/react';
import { useMemo, useRef } from 'react';

function toMetadata(thread: DbThread) {
  return {
    status: thread.is_archived ? ('archived' as const) : ('regular' as const),
    remoteId: thread.id,
    title: thread.title ?? undefined,
  };
}

/**
 * Thread-list metadata backed by our Postgres (via the backend `/chat`
 * endpoints). Per-thread message history is provided separately, inside the
 * runtime hook (see `useChatThreadRuntime` in chat-assistant), because the
 * remote-thread-list runtime calls the runtime hook outside this adapter's
 * `unstable_Provider`.
 */
export function useDbThreadListAdapter(): RemoteThreadListAdapter {
  const session = useSession();
  const tokenRef = useRef<string | undefined>(undefined);
  tokenRef.current = session.data?.accessToken;

  return useMemo<RemoteThreadListAdapter>(() => {
    const token = () => tokenRef.current;
    return {
      list: async () => {
        const rows = await chatThreadsApi.list(token());
        return { threads: rows.map(toMetadata) };
      },
      initialize: async () => {
        const thread = await chatThreadsApi.create(token());
        return { remoteId: thread.id, externalId: undefined };
      },
      rename: async (remoteId, newTitle) => {
        await chatThreadsApi.update(token(), remoteId, { title: newTitle });
      },
      archive: async (remoteId) => {
        await chatThreadsApi.update(token(), remoteId, { is_archived: true });
      },
      unarchive: async (remoteId) => {
        await chatThreadsApi.update(token(), remoteId, { is_archived: false });
      },
      delete: async (remoteId) => {
        await chatThreadsApi.remove(token(), remoteId);
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
          await chatThreadsApi.update(token(), remoteId, { title });
        } catch {
          // non-fatal
        }
        return createAssistantStream((controller) => {
          controller.appendText(title);
        });
      },
      fetch: async (remoteId) => {
        const rows = await chatThreadsApi.list(token());
        const thread = rows.find((row) => row.id === remoteId);
        if (!thread) throw new Error('Thread not found');
        return toMetadata(thread);
      },
    };
  }, []);
}
