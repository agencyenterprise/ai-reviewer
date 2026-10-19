import { describe, expect, it } from 'vitest';
import { TurnAccumulator, userMessage, type ChatMessage } from './turn';

function resumed(event: { name?: string }): ChatMessage[] {
  const turn = new TurnAccumulator(userMessage('', []));
  turn.apply({ t: 'tool_result', id: 'c1', result: 'Applied 7 of 8.', mid: 't1', ...event });
  return turn.assistantMessages;
}

describe('a resumed answer', () => {
  it('names the result of a call made before the stream began, as the backend sends it', () => {
    const [result] = resumed({ name: 'ask_to_apply' });

    expect(result).toMatchObject({ type: 'tool', tool_call_id: 'c1', name: 'ask_to_apply' });
  });
});
