'use client';

import { ReasoningPanel } from '@/components/assistant-ui/elements/reasoning-panel';
import type { ThreadComponents } from '@/components/assistant-ui/elements/thread.aui';
import { reasoningSteps } from '@/lib/chat/reasoning-steps';
import { useAuiState } from '@assistant-ui/react';
import { useMemo, useState } from 'react';

type ReasoningGroupComponent = NonNullable<ThreadComponents['ReasoningGroup']>;

/**
 * The `ReasoningGroup` slot of assistant-ui's Thread: a run of reasoning parts
 * shown as assistant-ui's step timeline (`ReasoningPanel`), one step per
 * summary heading.
 */
export const ReasoningSteps: ReasoningGroupComponent = ({ group }) => {
  const parts = useAuiState((s) => s.message.parts);
  const steps = useMemo(() => {
    const text = group.indices
      .map((index) => parts[index])
      .flatMap((part) => (part?.type === 'reasoning' ? [part.text] : []))
      .join('');
    return reasoningSteps(text);
  }, [group.indices, parts]);

  // Open while the model is thinking, until the user toggles it themselves.
  const streaming = group.status.type === 'running';
  const [userOpen, setUserOpen] = useState<boolean>();
  const seconds = group.timing?.completedAt
    ? Math.round((group.timing.completedAt - group.timing.startedAt) / 1000)
    : undefined;

  if (steps.length === 0) return null;

  return (
    <ReasoningPanel
      steps={steps}
      visibleSteps={steps.length}
      streaming={streaming}
      open={userOpen ?? streaming}
      onOpenChange={setUserOpen}
      restingLabel={seconds ? `Thought for ${seconds}s` : 'Reasoning'}
      className="max-w-none"
    />
  );
};
