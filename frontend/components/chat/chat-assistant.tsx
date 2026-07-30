'use client';

import { Thread } from '@/components/assistant-ui/thread';
import { DocumentAttachmentAdapter } from '@/components/chat/document-attachment-adapter';
import { DEFAULT_MODEL_ID } from '@/lib/chat-models';
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ChatModelRunResult,
  type ThreadMessage,
} from '@assistant-ui/react';
import { useMemo } from 'react';

// Mutable parts we accumulate while streaming; yielded as assistant-ui content.
type StreamPart =
  | { type: 'text'; text: string }
  | { type: 'reasoning'; text: string }
  | {
      type: 'tool-call';
      toolCallId: string;
      toolName: string;
      args: Record<string, unknown>;
      argsText: string;
      result?: unknown;
      isError?: boolean;
    };

// One NDJSON event from /api/chat.
type StreamEvent =
  | { t: 'text'; v: string }
  | { t: 'reasoning'; v: string }
  | { t: 'tool'; id: string; name: string; args?: Record<string, unknown> }
  | { t: 'tool_result'; id: string; result: unknown; isError?: boolean }
  | { t: 'error'; v: string };

// Stateless adapter; a single shared instance is fine.
const attachmentAdapter = new DocumentAttachmentAdapter();

/**
 * Flatten an assistant-ui message into plain text for the API, including the
 * text extracted from any attached documents (which the attachment adapter
 * stores as text parts on `message.attachments`).
 */
function messageToText(message: ThreadMessage): string {
  const bodyText = message.content.map((part) => (part.type === 'text' ? part.text : '')).join('');

  const attachmentText = (message.attachments ?? [])
    .flatMap((attachment) => attachment.content)
    .map((part) => (part.type === 'text' ? part.text : ''))
    .filter(Boolean)
    .join('\n\n');

  return [attachmentText, bodyText].filter(Boolean).join('\n\n');
}

const chatAdapter: ChatModelAdapter = {
  async *run({ messages, context, abortSignal }) {
    // The Model Selector (in the composer) publishes the chosen model into the
    // run's ModelContext as `config.modelName`.
    const model = context.config?.modelName ?? DEFAULT_MODEL_ID;

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        messages: messages.map((message) => ({
          role: message.role,
          content: messageToText(message),
        })),
      }),
      signal: abortSignal,
    });

    if (!response.ok || !response.body) {
      const detail = await response.text().catch(() => '');
      throw new Error(detail || `Chat request failed with status ${response.status}`);
    }

    const parts: StreamPart[] = [];

    const applyEvent = (event: StreamEvent) => {
      const last = parts[parts.length - 1];
      switch (event.t) {
        case 'text':
          if (last?.type === 'text') last.text += event.v;
          else parts.push({ type: 'text', text: event.v });
          break;
        case 'reasoning':
          if (last?.type === 'reasoning') last.text += event.v;
          else parts.push({ type: 'reasoning', text: event.v });
          break;
        case 'tool':
          parts.push({
            type: 'tool-call',
            toolCallId: event.id,
            toolName: event.name,
            args: event.args ?? {},
            argsText: JSON.stringify(event.args ?? {}),
          });
          break;
        case 'tool_result': {
          const call = parts.find((p) => p.type === 'tool-call' && p.toolCallId === event.id);
          if (call?.type === 'tool-call') {
            call.result = event.result;
            if (event.isError) call.isError = true;
          }
          break;
        }
        case 'error':
          throw new Error(event.v);
      }
    };

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const drainLines = (flush: boolean) => {
      let newlineIndex: number;
      while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, newlineIndex).trim();
        buffer = buffer.slice(newlineIndex + 1);
        if (line) applyEvent(JSON.parse(line) as StreamEvent);
      }
      if (flush && buffer.trim()) {
        applyEvent(JSON.parse(buffer.trim()) as StreamEvent);
        buffer = '';
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      drainLines(false);
      yield { content: parts } as ChatModelRunResult;
    }
    drainLines(true);
    yield { content: parts } as ChatModelRunResult;
  },
};

export function ChatAssistant() {
  const runtime = useLocalRuntime(
    chatAdapter,
    useMemo(() => ({ adapters: { attachments: attachmentAdapter } }), []),
  );

  return (
    <div className="h-[calc(100dvh-6.5rem)] overflow-hidden rounded-lg border bg-background">
      <AssistantRuntimeProvider runtime={runtime}>
        <Thread />
      </AssistantRuntimeProvider>
    </div>
  );
}
