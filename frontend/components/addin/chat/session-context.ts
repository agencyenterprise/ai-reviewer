import { AddinSession } from '@/components/addin/addin-sign-in';
import { createContext, useContext } from 'react';

/**
 * The signed-in session, for the parts assistant-ui renders on its own: a tool's card
 * is mounted by the thread, not by the pane, so it cannot be handed the session as a prop.
 */
export const AddinSessionContext = createContext<AddinSession | null>(null);

export function useAddinSession(): AddinSession {
  const session = useContext(AddinSessionContext);
  if (!session) throw new Error('useAddinSession needs an AddinSessionContext provider');
  return session;
}

/** The answer paused on a card, if any, and how to carry it on once that card is settled. */
export type PausedAnswer = {
  pendingSuggestionId: string | null;
  resume: () => Promise<void>;
  /** The answer is carrying on after its card: the card stays in view meanwhile. */
  resuming: boolean;
};

export const PausedAnswerContext = createContext<PausedAnswer>({
  pendingSuggestionId: null,
  resume: async () => {},
  resuming: false,
});

export function usePausedAnswer(): PausedAnswer {
  return useContext(PausedAnswerContext);
}
