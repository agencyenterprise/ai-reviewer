'use client';

import { ReadonlyThread } from '@/components/assistant-ui/readonly-thread';
import { AssistantRuntimeProvider, useExternalMessageConverter, useExternalStoreRuntime } from '@assistant-ui/react';
import { convertLangChainMessages, LangChainMessage } from '@assistant-ui/react-langgraph';
import { useMemo } from 'react';

/**
 * A run's agent conversation, read-only: what it read and how it worked its way
 * to its results.
 */
export function AgentTranscript({ messages }: { messages: unknown[] }) {
  const langChainMessages = useMemo(() => messages as LangChainMessage[], [messages]);

  // The converter joins each tool result into its tool call (so finished calls
  // read as done) and merges consecutive steps into one assistant message.
  const threadMessages = useExternalMessageConverter<LangChainMessage>({
    callback: convertLangChainMessages,
    messages: langChainMessages,
    isRunning: false,
  });

  const runtime = useExternalStoreRuntime({
    messages: threadMessages,
    isRunning: false,
    onNew: async () => {},
  });

  return (
    // No top padding: the tabs above already space the panel from their list.
    <AssistantRuntimeProvider runtime={runtime}>
      <ReadonlyThread viewportClassName="pt-0" />
    </AssistantRuntimeProvider>
  );
}
