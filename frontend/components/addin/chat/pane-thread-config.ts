import type { ThreadComponents } from '@/components/assistant-ui/elements/thread.aui';
import { ReasoningSteps } from '@/components/assistant-ui/reasoning-steps';
import { AuiConfig, Tools, type Toolkit } from '@assistant-ui/react';
import { ChecksMenu, CheckSlashPopover } from './pane-checks';
import { PaneWelcome } from './pane-welcome';
import { SuggestChangesPart } from './suggestion-card';

/**
 * The pane's text sizes, a step down from /chat's for a pane about 320px wide. Each one
 * named, on the thread's root:
 * - message text (the user's and the agent's): 14px, from the page's 16px;
 * - the agent's markdown headings: h1 and h2 16px (from 20px and 18px), h3 and h4 14px
 *   (from 16px); h5 and h6 are already 14px;
 * - the message box: 14px, from 16px.
 * Cards, the welcome and the checks list set their own sizes.
 */
export const PANE_THREAD_CLASS = [
  'text-sm',
  '[&_.aui-md-h1]:text-base',
  '[&_.aui-md-h2]:text-base',
  '[&_.aui-md-h3]:text-sm',
  '[&_.aui-md-h4]:text-sm',
  '[&_.aui-composer-input]:text-sm',
].join(' ');

// Module scope, so Thread's message subtrees don't re-render with this component. /chat's
// thread, with the pane's welcome and composer additions.
export const PANE_THREAD_COMPONENTS: ThreadComponents = {
  className: PANE_THREAD_CLASS,
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
