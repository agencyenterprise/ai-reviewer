'use client';

import { AddinSession } from '@/components/addin/addin-sign-in';
import { Button } from '@/components/ui/button';
import { Thread } from '@/components/assistant-ui/elements/thread.aui';
import { chatDocumentKey } from '@/lib/addin/pane-document';
import { AssistantRuntimeProvider, useAuiState } from '@assistant-ui/react';
import { UseMutationResult } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { PANE_CONFIG, PANE_THREAD_COMPONENTS } from './pane-thread-config';
import { AddinSessionContext, PausedAnswerContext } from './session-context';
import { useWordChatRuntime } from './use-word-chat-runtime';

/**
 * The pane's chat with Draft Detective about the open document: one continuing
 * conversation per document, which "New chat" sets aside to start again.
 */
export function WordChat({ session }: { session: AddinSession }) {
  const documentUrl = chatDocumentKey(typeof Office !== 'undefined' ? (Office.context.document?.url ?? '') : '');
  const { runtime, clear, resume, resuming, pendingSuggestionId, historyError } = useWordChatRuntime(
    session,
    documentUrl,
  );
  const paused = useMemo(() => ({ pendingSuggestionId, resume, resuming }), [pendingSuggestionId, resume, resuming]);

  return (
    <AddinSessionContext.Provider value={session}>
      <PausedAnswerContext.Provider value={paused}>
        <AssistantRuntimeProvider runtime={runtime} config={PANE_CONFIG}>
          <div className="flex min-h-0 flex-1 flex-col">
            <ChatHeader clear={clear} failed={!!historyError} />
            <div className="min-h-0 flex-1">
              <Thread components={PANE_THREAD_COMPONENTS} />
            </div>
          </div>
        </AssistantRuntimeProvider>
      </PausedAnswerContext.Provider>
    </AddinSessionContext.Provider>
  );
}

type ChatHeaderProps = {
  clear: UseMutationResult<unknown, Error, void>;
  failed: boolean;
};

/** "New chat", asked twice: a cleared conversation cannot be brought back from the pane. */
function ChatHeader({ clear, failed }: ChatHeaderProps) {
  const isRunning = useAuiState((s) => s.thread.isRunning);
  const isEmpty = useAuiState((s) => s.thread.isEmpty);
  const [confirming, setConfirming] = useState(false);

  return (
    <div className="flex min-h-8 items-center justify-between gap-2 border-b px-3 py-1 text-xs">
      {confirming ? (
        <>
          <span>Clear this chat? It cannot be reopened.</span>
          <span className="flex gap-1">
            <Button
              size="sm"
              variant="destructive"
              className="h-6 px-2 text-xs"
              disabled={clear.isPending}
              onClick={() => clear.mutate(undefined, { onSettled: () => setConfirming(false) })}
            >
              {clear.isPending ? 'Clearing…' : 'Clear'}
            </Button>
            <Button size="sm" variant="ghost" className="h-6 px-2 text-xs" onClick={() => setConfirming(false)}>
              Cancel
            </Button>
          </span>
        </>
      ) : (
        <>
          <span className="text-muted-foreground">
            {failed ? 'Could not load the conversation.' : 'Chat about this document'}
          </span>
          <Button
            size="sm"
            variant="ghost"
            className="h-6 px-2 text-xs"
            onClick={() => setConfirming(true)}
            disabled={isRunning || isEmpty}
          >
            New chat
          </Button>
        </>
      )}
    </div>
  );
}
