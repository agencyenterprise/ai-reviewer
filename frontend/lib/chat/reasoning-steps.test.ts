import { describe, expect, it } from 'vitest';
import { reasoningSteps } from '@/lib/chat/reasoning-steps';

describe('reasoningSteps', () => {
  it('turns a headed summary into one step', () => {
    expect(reasoningSteps('**Reading the request**\n\nThe user wants a short answer.')).toEqual([
      { title: 'Reading the request', body: 'The user wants a short answer.' },
    ]);
  });

  it('splits sections the backend joined without a separator', () => {
    const text = '**Reading the skill**\n\nI should open SKILL.md first.**Answering**\n\nOne sentence is enough.';
    expect(reasoningSteps(text)).toEqual([
      { title: 'Reading the skill', body: 'I should open SKILL.md first.' },
      { title: 'Answering', body: 'One sentence is enough.' },
    ]);
  });

  it('keeps text without a heading as a step under the fallback title', () => {
    expect(reasoningSteps('Plain thoughts.')).toEqual([{ title: 'Thinking', body: 'Plain thoughts.' }]);
  });

  it('keeps text before the first heading', () => {
    expect(reasoningSteps('Warming up.\n**Plan**\n\nRead the file.')).toEqual([
      { title: 'Thinking', body: 'Warming up.' },
      { title: 'Plan', body: 'Read the file.' },
    ]);
  });

  it('leaves inline bold inside a body alone', () => {
    expect(reasoningSteps('**Plan**\n\nCheck the **main** file.')).toEqual([
      { title: 'Plan', body: 'Check the **main** file.' },
    ]);
  });

  it('shows a heading whose body has not streamed yet', () => {
    expect(reasoningSteps('**Plan**\n')).toEqual([{ title: 'Plan', body: '' }]);
  });

  it('returns no steps for empty text', () => {
    expect(reasoningSteps('')).toEqual([]);
  });
});
