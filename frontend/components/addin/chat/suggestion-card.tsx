'use client';

import { Button } from '@/components/ui/button';
import { AppliedSummary, HandoffCard } from '@/components/addin/handoff-card';
import { describeItems } from '@/lib/addin/item-counts';
import { isApiError } from '@/lib/api-error';
import { ChatSuggestion, getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet } from '@/lib/generated-api';
import { useAuiState, type AssistantState, type ToolCallMessagePartComponent } from '@assistant-ui/react';
import { useQuery } from '@tanstack/react-query';
import { useAddinSession, usePausedAnswer } from './session-context';

type ToolResult = { saved?: boolean; suggestion_id?: string; card?: 'new' | 'added'; message?: string };

/** The tool's result, which is JSON (`lib/agents/tools/word_suggestions.py`). */
export function suggestionResult(result: unknown): ToolResult | null {
  if (result && typeof result === 'object') return result as ToolResult;
  if (typeof result !== 'string') return null;
  try {
    return JSON.parse(result) as ToolResult;
  } catch {
    return null;
  }
}

/**
 * The card a `suggest_changes` call shows, if any: its id, or null.
 *
 * One answer has one card (`lib/agents/tools/word_suggestions.py`): the call that opened
 * it shows it, and later calls that only added to it show nothing. Nothing either while
 * the answer is still being written, since calls may still be adding to it, except the
 * card it waited on before carrying on (`keep`), which is settled; and nothing for a call
 * that stored nothing, whose reply is for the agent (fix these quotes, try again).
 */
export function cardToShow(result: unknown, answerInProgress: boolean, keep: string | null = null): string | null {
  const parsed = suggestionResult(result);
  if (!parsed?.saved || !parsed.suggestion_id || parsed.card === 'added') return null;
  if (answerInProgress && parsed.suggestion_id !== keep) return null;
  return parsed.suggestion_id;
}

/** Whether this message belongs to the answer still being written: after the last question. */
function inAnswerInProgress(state: AssistantState): boolean {
  if (!state.thread.isRunning) return false;
  const messages = state.thread.messages;
  const mine = messages.findIndex((message) => message.id === state.message.id);
  const lastQuestion = messages.findLastIndex((message) => message.role === 'user');
  return mine > lastQuestion;
}

/** What the agent's `suggest_changes` call shows in the chat: the answer's card, once. */
export const SuggestChangesPart: ToolCallMessagePartComponent = ({ result }) => {
  const inProgress = useAuiState(inAnswerInProgress);
  const { resumedCard } = usePausedAnswer();
  const id = cardToShow(result, inProgress, resumedCard);
  return id ? <SuggestionCard id={id} /> : null;
};

/**
 * One set of suggestions, as it stands on the server: Apply and Dismiss while it is
 * open, and what became of it once it is not. Applying, claiming and reporting are the
 * Teams handoff card's own, since a suggestion is stored as a handoff.
 */
export function SuggestionCard({ id }: { id: string }) {
  const { email, authorize, expire } = useAddinSession();
  const { pendingSuggestionId, resume, resuming } = usePausedAnswer();
  const suggestion = useQuery({
    queryKey: ['addin-suggestion', email, id],
    queryFn: async () => {
      try {
        return await getSuggestionApiMicrosoftWordChatSuggestionsSuggestionIdGet({
          path: { suggestion_id: id },
          headers: { Authorization: await authorize() },
        });
      } catch (error) {
        if (isApiError(error, 401)) expire();
        throw error;
      }
    },
    retry: false,
    // Refetching when the pane regains focus would land mid-Apply, while the card is
    // `applying` on the server; the card refetches itself once it is settled.
    refetchOnWindowFocus: false,
  });

  if (suggestion.isLoading) return <Frame>Loading suggestions…</Frame>;
  if (isApiError(suggestion.error, 404)) {
    return <Frame>These suggestions are no longer available: they are kept for a week.</Frame>;
  }
  if (suggestion.error || !suggestion.data) return <Frame>Could not load these suggestions.</Frame>;

  const data = suggestion.data;
  const waitedOn = pendingSuggestionId === id;
  // Settled: show what became of it, and if the answer was waiting on this card, let the
  // agent carry on with the outcome. Only once the server has it settled: a card another
  // pane is still applying would be refused.
  const settle = async () => {
    const fresh = await suggestion.refetch();
    if (waitedOn && fresh.data && !isOpen(fresh.data.status)) await resume();
  };
  const refetch = () => void settle();
  const { status } = data;
  if (status === 'pending' || status === 'applying') {
    return (
      <Frame>
        <HandoffCard
          handoff={{ ...data, status }}
          source="chat"
          authorize={authorize}
          onExpired={expire}
          onDone={refetch}
          onReported={refetch}
        />
      </Frame>
    );
  }
  return (
    <Frame>
      {settled(data)}
      {/* The answer still waits on this card: a resume that failed (the network, a
          sign-in that expired, a reload) can be tried again from here. */}
      {waitedOn && (
        <Button size="sm" className="mt-2" onClick={() => void resume()} disabled={resuming}>
          {resuming ? 'Continuing…' : 'Continue'}
        </Button>
      )}
    </Frame>
  );
}

function isOpen(status: ChatSuggestion['status']): boolean {
  return status === 'pending' || status === 'applying';
}

function settled(data: ChatSuggestion) {
  if (data.status === 'dismissed') {
    const comments = data.items.comments?.length ?? 0;
    const edits = data.items.edits?.length ?? 0;
    return <p className="text-xs text-muted-foreground">Dismissed: {describeItems(comments, edits)} not added.</p>;
  }
  const items = (data.outcome?.items ?? []).map((item, index) => ({ ...item, index, detail: item.detail ?? '' }));
  return <AppliedSummary items={items} sent destination="the chat" />;
}

function Frame({ children }: { children: React.ReactNode }) {
  return <div className="my-2 rounded-lg border bg-card p-3 text-[13px]">{children}</div>;
}
