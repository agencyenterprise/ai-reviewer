import { describe, expect, it, vi } from 'vitest';
import { AssistantRuntimeProvider, useExternalMessageConverter, useExternalStoreRuntime } from '@assistant-ui/react';
import { renderInto } from '@/lib/test-render';
import { convertChatMessage, TurnAccumulator, userMessage, type ChatMessage } from './turn';

const HISTORY: ChatMessage[] = [
  { id: 'u1', type: 'human', content: 'Fix it' },
  {
    id: 'a1',
    type: 'ai',
    content: [],
    tool_calls: [{ id: 'c1', name: 'ask_to_apply', args: { suggestion_id: 's1' } }],
  },
];

function resumedTurn(name?: string): ChatMessage[] {
  const turn = new TurnAccumulator(userMessage('', []));
  turn.apply({ t: 'tool_result', id: 'c1', result: 'Applied 7 of 8.', mid: 't1', ...(name ? { name } : {}) });
  return turn.assistantMessages;
}

function Harness({ inflight }: { inflight: ChatMessage[] }) {
  const messages = useExternalMessageConverter({
    callback: convertChatMessage,
    messages: [...HISTORY, ...inflight],
    isRunning: true,
  });
  const runtime = useExternalStoreRuntime({ messages, isRunning: true, onNew: async () => {} });
  return <AssistantRuntimeProvider runtime={runtime}>{null}</AssistantRuntimeProvider>;
}

describe('a resumed answer, shown with the stored call it answers', () => {
  it('renders when the result carries the tool name the backend sends', async () => {
    await expect(renderInto(<Harness inflight={resumedTurn('ask_to_apply')} />)).resolves.toBeDefined();
  });

  it('is what crashed the pane when the name had to be guessed', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    await expect(renderInto(<Harness inflight={resumedTurn()} />)).rejects.toThrow(/does not match existing tool call/);
  });
});
