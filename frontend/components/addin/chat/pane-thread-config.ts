import type { ThreadComponents } from '@/components/assistant-ui/elements/thread.aui';
import { ReasoningSteps } from '@/components/assistant-ui/reasoning-steps';
import { AuiConfig, Tools, type Toolkit } from '@assistant-ui/react';
import { ChecksMenu, CheckSlashPopover } from './pane-checks';
import { PaneWelcome } from './pane-welcome';
import { SuggestChangesPart } from './suggestion-card';

// Module scope, so Thread's message subtrees don't re-render with this component. /chat's
// thread, with the pane's welcome and composer additions.
export const PANE_THREAD_COMPONENTS: ThreadComponents = {
  Welcome: PaneWelcome,
  ReasoningGroup: ReasoningSteps,
  ComposerTools: ChecksMenu,
  SlashPopover: CheckSlashPopover,
  composerPlaceholder: 'Ask about this document, or type / for checks',
};

// The agent's suggestions are a card to act on, not a step of its working, so they are
// shown on their own rather than folded into the chain of thought.
// `ask_to_apply` is the agent waiting on that same card: the card is the question, so the
// call itself shows nothing.
const TOOLKIT: Toolkit = {
  suggest_changes: { type: 'backend', display: 'standalone', render: SuggestChangesPart },
  ask_to_apply: { type: 'backend', display: 'standalone', render: () => null },
};
export const PANE_CONFIG = AuiConfig({ tools: Tools({ toolkit: TOOLKIT }) });
